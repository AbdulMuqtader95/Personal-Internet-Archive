import os
import tempfile

import numpy as np
from fastapi.testclient import TestClient

from archive import main


def fake_fetch(url):
    return {"url": url, "title": "Page " + url[-1], "text": "hello tags " * 20, "html": "<p>x</p>"}


def fake_embed(texts):
    return [np.zeros(384, dtype=np.float32) for _ in texts]


main.fetch_and_extract = fake_fetch
main.embed = fake_embed


def run():
    client = TestClient(main.app)

    for u in ("https://fake.test/a", "https://fake.test/b"):
        assert client.post("/save", json={"url": u}).status_code == 200
    pages = {p["url"]: p for p in client.get("/pages").json()}
    a, b = pages["https://fake.test/a"]["id"], pages["https://fake.test/b"]["id"]
    chunks_before = pages["https://fake.test/a"]["chunks"]
    assert all(p["tags"] == [] for p in pages.values())
    print("ok: pages start with no tags")

    # adding normalizes the tag
    r = client.post(f"/pages/{a}/tags", json={"tag": "  Python "})
    assert r.status_code == 200 and r.json()["tag"] == "python"
    # duplicates are ignored, not duplicated
    assert client.post(f"/pages/{a}/tags", json={"tag": "python"}).status_code == 200
    assert client.post(f"/pages/{a}/tags", json={"tag": "machine learning"}).status_code == 200
    page_a = next(p for p in client.get("/pages").json() if p["id"] == a)
    assert page_a["tags"] == ["machine learning", "python"], page_a["tags"]
    print("ok: tags added, normalized, no duplicates")

    # tags must not change the chunk count (join-multiplication bug)
    assert page_a["chunks"] == chunks_before
    print("ok: chunk count unchanged by tags")

    # bad requests
    assert client.post(f"/pages/{a}/tags", json={"tag": "   "}).status_code == 404
    assert client.post("/pages/99999/tags", json={"tag": "x"}).status_code == 404
    print("ok: empty tag and missing page rejected")

    # filter
    assert [p["id"] for p in client.get("/pages", params={"tag": "python"}).json()] == [a]
    assert client.get("/pages", params={"tag": "PYTHON"}).json()[0]["id"] == a
    assert client.get("/pages", params={"tag": "nope"}).json() == []
    assert len(client.get("/pages").json()) == 2
    print("ok: ?tag= filter works")

    # re-saving a URL keeps its tags
    assert client.post("/save", json={"url": "https://fake.test/a"}).status_code == 200
    page_a = next(p for p in client.get("/pages").json() if p["id"] == a)
    assert "python" in page_a["tags"]
    print("ok: tags survive re-save")

    # remove a tag (including one with a space)
    assert client.delete(f"/pages/{a}/tags/machine%20learning").status_code == 200
    assert client.delete(f"/pages/{a}/tags/machine%20learning").status_code == 404
    print("ok: tag removed, second removal is 404")

    # deleting a page removes its tags
    assert client.delete(f"/pages/{a}").status_code == 200
    assert client.get("/pages", params={"tag": "python"}).json() == []
    con = main.init_db()
    assert con.execute("SELECT COUNT(*) FROM tags WHERE page_id = ?", (a,)).fetchone()[0] == 0
    con.close()
    print("ok: tags deleted with the page")


if __name__ == "__main__":
    original = os.getcwd()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        os.chdir(tmp)
        try:
            run()
        finally:
            os.chdir(original)
    print("all tag tests passed")
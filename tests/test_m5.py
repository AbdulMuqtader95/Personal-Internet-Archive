import os
import tempfile

import numpy as np
from fastapi.testclient import TestClient

from archive import main

FAKE_HTML = "<html><head><title>Fake</title></head><body><p>hello snapshot</p></body></html>"


def fake_fetch(url):
    return {"url": url, "title": "Fake page", "text": "hello snapshot " * 20, "html": FAKE_HTML}


def fake_embed(texts):
    return [np.zeros(384, dtype=np.float32) for _ in texts]


# no real network, no real model
main.fetch_and_extract = fake_fetch
main.embed = fake_embed


def run():
    client = TestClient(main.app)

    # save a page, then fetch its snapshot
    r = client.post("/save", json={"url": "https://fake.test/a"})
    assert r.status_code == 200, r.text
    page_id = client.get("/pages").json()[0]["id"]

    r = client.get(f"/pages/{page_id}/snapshot")
    assert r.status_code == 200
    assert r.text == FAKE_HTML
    assert r.headers["content-security-policy"] == "sandbox"
    print("ok: snapshot stored, served, sandboxed")

    # re-saving the same URL keeps a single snapshot
    r = client.post("/save", json={"url": "https://fake.test/a"})
    assert r.status_code == 200
    assert client.get(f"/pages/{page_id}/snapshot").status_code == 200
    print("ok: re-save works")

    # deleting the page removes the snapshot
    assert client.delete(f"/pages/{page_id}").status_code == 200
    assert client.get(f"/pages/{page_id}/snapshot").status_code == 404
    print("ok: snapshot gone after delete")

    # unknown id gives a clean 404
    assert client.get("/pages/99999/snapshot").status_code == 404
    print("ok: missing snapshot returns 404")


if __name__ == "__main__":
    original = os.getcwd()
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        os.chdir(tmp)  # archive.db is created here, not in your project
        try:
            run()
        finally:
            os.chdir(original)
    print("all M5 tests passed")
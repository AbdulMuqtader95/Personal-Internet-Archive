import sqlite3
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .fetch import fetch_and_extract
from .db import init_db, save_page, save_chunks, search, semantic_search
from .chunk import chunk_text
from .embed import embed

app = FastAPI(title="Personal Internet Archive")


class SaveRequest(BaseModel):
    url: str


@app.post("/save")
def save(req: SaveRequest):
    try:
        page = fetch_and_extract(req.url)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Could not fetch URL: {e}")
    con = init_db()
    try:
        save_page(con, page)
        page_id = con.execute(
            "SELECT id FROM pages WHERE url = ?", (page["url"],)
        ).fetchone()[0]
        chunks = chunk_text(page["text"])
        vectors = embed(chunks) if chunks else []
        save_chunks(con, page_id, chunks, vectors)
    finally:
        con.close()
    return {
        "url": page["url"],
        "title": page["title"],
        "chars": len(page["text"]),
        "chunks": len(chunks),
    }


@app.get("/search")
def search_pages(q: str, limit: int = 10):
    con = init_db()
    try:
        rows = search(con, q, limit)
    except sqlite3.OperationalError:
        raise HTTPException(status_code=400, detail="Invalid search query")
    finally:
        con.close()
    return [{"url": u, "title": t, "snippet": s} for u, t, s in rows]

@app.get("/semantic-search")
def semantic(q: str, limit: int = 5):
    con = init_db()
    try:
        qvec = embed([q])[0]
        return semantic_search(con, qvec, limit)
    finally:
        con.close()
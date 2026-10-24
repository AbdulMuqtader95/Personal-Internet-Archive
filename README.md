# Personal Internet Archive

A self-hosted archive for web pages. Save a URL, and the page's text is extracted and stored locally so you can search it later. Keyword search works today; search by meaning (semantic search) is in progress.

## Features

- Save any web page by URL and extract its readable text
- Store pages locally in SQLite
- Full-text search with highlighted snippets (SQLite FTS5)
- Re-saving a URL updates the stored copy instead of duplicating it
- REST API with interactive docs (FastAPI)

## Tech stack

| Piece | Tool |
|---|---|
| Language | Python 3.11 |
| API | FastAPI + Uvicorn |
| Fetching | httpx |
| Text extraction | trafilatura |
| Storage and keyword search | SQLite with FTS5 |

## Getting started

```bash
conda create -n pia python=3.11 -y
conda activate pia
pip install fastapi uvicorn httpx trafilatura
python -m uvicorn archive.main:app --reload
```

Then open <http://127.0.0.1:8000/docs> to try the API.

> Some sites reject requests without an identifying User-Agent (Wikipedia is one). Edit `HEADERS` in `archive/fetch.py` and add your own contact details before saving pages.

## API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/save` | Body: `{"url": "https://..."}`. Fetches, extracts and stores the page. |
| GET | `/search?q=term&limit=10` | Keyword search. Returns URL, title and a highlighted snippet. |

## Project structure

```
archive/
├── fetch.py   # download a page and extract its text
├── db.py      # SQLite storage and FTS5 search
└── main.py    # FastAPI app
test_m1.py     # quick end-to-end check of fetch, store and search
```

## Roadmap

- [x] **M1:** save, extract, store and keyword search
- [ ] **M2:** chunk pages, generate embeddings locally, search by meaning
- [ ] **M3:** simple web UI, tags, raw HTML snapshots

## Why this project

It is the retrieval layer for a larger project: an agentic RAG assistant that reasons over the archive.

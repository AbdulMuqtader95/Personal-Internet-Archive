import sqlite3
import numpy as np

def init_db(path="archive.db"):
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS snapshots (
        page_id INTEGER PRIMARY KEY,
        html TEXT,
        saved_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS pages (
        id INTEGER PRIMARY KEY,
        url TEXT UNIQUE,
        title TEXT,
        text TEXT,
        saved_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts
        USING fts5(title, text, content='pages', content_rowid='id');
    CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY,
        page_id INTEGER,
        idx INTEGER,
        text TEXT,
        embedding BLOB
    );
    """)
    return con


def save_page(con, page):
    row = con.execute(
        "SELECT id, title, text FROM pages WHERE url = ?", (page["url"],)
    ).fetchone()
    if row:
        # remove the old FTS entry using the old values, then update in place
        con.execute(
            "INSERT INTO pages_fts (pages_fts, rowid, title, text) VALUES ('delete', ?, ?, ?)",
            row,
        )
        con.execute(
            "UPDATE pages SET title = ?, text = ?, saved_at = CURRENT_TIMESTAMP WHERE id = ?",
            (page["title"], page["text"], row[0]),
        )
        rowid = row[0]
    else:
        cur = con.execute(
            "INSERT INTO pages (url, title, text) VALUES (?, ?, ?)",
            (page["url"], page["title"], page["text"]),
        )
        rowid = cur.lastrowid
    con.execute(
        "INSERT INTO pages_fts (rowid, title, text) VALUES (?, ?, ?)",
        (rowid, page["title"], page["text"]),
    )
    con.commit()

def search(con, query, limit=10):
    return con.execute(
        "SELECT p.url, p.title, snippet(pages_fts, 1, '[', ']', '…', 12) "
        "FROM pages_fts JOIN pages p ON p.id = pages_fts.rowid "
        "WHERE pages_fts MATCH ? ORDER BY rank LIMIT ?",
        (query, limit),
    ).fetchall()

def save_chunks(con, page_id, chunks, vectors):
    con.execute("DELETE FROM chunks WHERE page_id = ?", (page_id,))
    con.executemany(
        "INSERT INTO chunks (page_id, idx, text, embedding) VALUES (?, ?, ?, ?)",
        [(page_id, i, c, v.tobytes()) for i, (c, v) in enumerate(zip(chunks, vectors))],
    )
    con.commit()

def save_snapshot(con, page_id, html):
    con.execute(
        "INSERT OR REPLACE INTO snapshots (page_id, html) VALUES (?, ?)",
        (page_id, html),
    )
    con.commit()

def get_snapshot(con, page_id):
    row = con.execute(
        "SELECT html FROM snapshots WHERE page_id = ?", (page_id,)
    ).fetchone()
    return row[0] if row else None

def semantic_search(con, query_vec, limit=5, min_score=0.25):
    rows = con.execute(
        "SELECT c.text, c.embedding, p.url, p.title "
        "FROM chunks c JOIN pages p ON p.id = c.page_id"
    ).fetchall()
    if not rows:
        return []
    matrix = np.vstack([np.frombuffer(r[1], dtype=np.float32) for r in rows])
    scores = matrix @ query_vec
    results, seen = [], set()
    for i in np.argsort(-scores):
        if scores[i] < min_score:
            break
        url = rows[i][2]
        if url in seen:
            continue
        seen.add(url)
        results.append({
            "url": url,
            "title": rows[i][3],
            "score": float(scores[i]),
            "chunk": rows[i][0][:400],
        })
        if len(results) == limit:
            break
    return results

def list_pages(con):
    return con.execute(
        "SELECT p.id, p.title, p.url, p.saved_at, COUNT(c.id) "
        "FROM pages p LEFT JOIN chunks c ON c.page_id = p.id "
        "GROUP BY p.id ORDER BY p.saved_at DESC, p.id DESC"
    ).fetchall()

def delete_page(con, page_id):
    row = con.execute(
        "SELECT title, text FROM pages WHERE id = ?", (page_id,)
    ).fetchone()
    if row is None:
        return False
    # remove the keyword-search entry (needs the original values)
    con.execute(
        "INSERT INTO pages_fts (pages_fts, rowid, title, text) VALUES ('delete', ?, ?, ?)",
        (page_id, row[0], row[1]),
    )
    con.execute("DELETE FROM chunks WHERE page_id = ?", (page_id,))
    con.execute("DELETE FROM snapshots WHERE page_id = ?", (page_id,))
    con.execute("DELETE FROM pages WHERE id = ?", (page_id,))
    con.commit()
    return True
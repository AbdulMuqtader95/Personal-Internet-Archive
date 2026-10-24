import sqlite3

def init_db(path="archive.db"):
    con = sqlite3.connect(path)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS pages (
        id INTEGER PRIMARY KEY,
        url TEXT UNIQUE,
        title TEXT,
        text TEXT,
        saved_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts
        USING fts5(title, text, content='pages', content_rowid='id');
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
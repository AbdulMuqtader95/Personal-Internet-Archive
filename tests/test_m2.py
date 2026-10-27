from archive.db import init_db, save_chunks, semantic_search
from archive.chunk import chunk_text
from archive.embed import embed

con = init_db()

for page_id, title, text in con.execute("SELECT id, title, text FROM pages").fetchall():
    chunks = chunk_text(text)
    save_chunks(con, page_id, chunks, embed(chunks))
    print(title, "->", len(chunks), "chunks")

query = embed(["how do computers find files shared by other users"])[0]
for r in semantic_search(con, query, limit=3):
    print(round(r["score"], 3), r["title"], "|", r["chunk"][:120])
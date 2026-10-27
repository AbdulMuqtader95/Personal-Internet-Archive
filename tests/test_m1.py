from archive.fetch import fetch_and_extract
from archive.db import init_db, save_page, search

con = init_db()

for url in [
    "https://en.wikipedia.org/wiki/BitTorrent",
    "https://en.wikipedia.org/wiki/Semantic_search",
]:
    page = fetch_and_extract(url)
    print(page["title"], "-", len(page["text"]), "chars")
    save_page(con, page)

for row in search(con, "peer"):
    print(row)
import httpx
import trafilatura

HEADERS = {
    "User-Agent": "PersonalInternetArchive/0.1 (personal learning project; abdulsfakemail@gmail.com)"
}

def fetch_and_extract(url: str) -> dict:
    resp = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=15)
    resp.raise_for_status()
    html = resp.text
    text = trafilatura.extract(html) or ""
    meta = trafilatura.extract_metadata(html)
    return {
        "url": str(resp.url),
        "title": (meta.title if meta and meta.title else url),
        "text": text,
        "html": html,
    }
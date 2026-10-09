import io
import re
from urllib.parse import urlparse, parse_qs

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi

from app.services.embeddings import Source

# HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ResearchAgent/1.0"}
HEADERS = {
    "User-Agent": "ResearchAgentBot/1.0 (student project; contact: salamlakhan7@gmail.com) httpx",
    "Accept-Language": "en",
}
MAX_CHARS = 20000   # cap per source
MIN_CHARS = 200     # below this, treat the page as unreadable


def _youtube_id(url: str) -> str | None:
    p = urlparse(url)
    if p.hostname in ("youtu.be",):
        return p.path.lstrip("/")
    if p.hostname and "youtube.com" in p.hostname:
        return parse_qs(p.query).get("v", [None])[0]
    return None


def _load_youtube(url: str, vid: str) -> Source:
    api = YouTubeTranscriptApi()
    fetched = api.fetch(vid)
    text = " ".join(s.text for s in fetched)
    return Source(url=url, title=f"YouTube video {vid}", text=text[:MAX_CHARS])


def _load_pdf(url: str, content: bytes) -> Source:
    reader = PdfReader(io.BytesIO(content))
    text = " ".join((page.extract_text() or "") for page in reader.pages)
    return Source(url=url, title=url.split("/")[-1], text=text[:MAX_CHARS])


def _load_html(url: str, html: str) -> Source:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()
    title = soup.title.string.strip() if soup.title and soup.title.string else url
    text = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
    return Source(url=url, title=title, text=text[:MAX_CHARS])


def load_source(url: str) -> tuple[Source | None, str | None]:
    """Returns (Source, None) on success or (None, reason) on failure."""
    try:
        vid = _youtube_id(url)
        if vid:
            src = _load_youtube(url, vid)
        else:
            r = httpx.get(url, headers=HEADERS, timeout=20, follow_redirects=True)
            if r.status_code >= 400:
                return None, f"HTTP {r.status_code} (blocked or not found)"
            ctype = r.headers.get("content-type", "")
            if "pdf" in ctype or url.lower().endswith(".pdf"):
                src = _load_pdf(url, r.content)
            else:
                src = _load_html(url, r.text)

        if len(src.text) < MIN_CHARS:
            return None, "Very little readable text (page may be JavaScript-loaded or blocked)"
        return src, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def load_many(urls: list[str]) -> tuple[list[Source], dict[str, str]]:
    """Load several URLs. Returns (sources, {failed_url: reason})."""
    sources, failed = [], {}
    for u in urls:
        src, err = load_source(u.strip())
        if src:
            sources.append(src)
        else:
            failed[u] = err
    return sources, failed
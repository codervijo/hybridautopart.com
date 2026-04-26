import random
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup

from lib.io import log, utc_now


class RobotsChecker:
    """Wraps stdlib RobotFileParser. If robots.txt is unreachable, allows everything."""

    def __init__(self, base_url: str, user_agent: str) -> None:
        self.user_agent = user_agent
        self._rp: urllib.robotparser.RobotFileParser | None = urllib.robotparser.RobotFileParser()
        robots_url = urllib.parse.urljoin(base_url, "/robots.txt")
        self._rp.set_url(robots_url)
        try:
            self._rp.read()
        except Exception as e:
            log(f"  robots.txt: read failed ({e}); allowing all")
            self._rp = None

    def can_fetch(self, url: str) -> bool:
        if self._rp is None:
            return True
        return self._rp.can_fetch(self.user_agent, url)


class RateLimiter:
    """Sleep enough between calls to keep at most one request per (delay + jitter) seconds."""

    def __init__(self, delay_s: float, jitter_s: float = 0.0) -> None:
        self.delay_s = delay_s
        self.jitter_s = jitter_s
        self._last_at: float = 0.0

    def wait(self) -> None:
        target = self.delay_s + random.uniform(0.0, self.jitter_s)
        elapsed = time.monotonic() - self._last_at
        if elapsed < target:
            time.sleep(target - elapsed)
        self._last_at = time.monotonic()


def fetch_sitemap(sitemap_url: str, user_agent: str, timeout: int = 30) -> list[str]:
    """Fetch a sitemap URL (or sitemap index) and return all <loc> URLs found."""
    urls: list[str] = []
    queue: list[str] = [sitemap_url]
    seen: set[str] = set()

    while queue:
        current = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)
        try:
            req = urllib.request.Request(current, headers={"User-Agent": user_agent})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
        except Exception as e:
            log(f"  sitemap fetch failed: {current} — {e}")
            continue
        try:
            root = ET.fromstring(data)
        except ET.ParseError as e:
            log(f"  sitemap parse failed: {current} — {e}")
            continue
        ns = root.tag.split("}")[0] + "}" if "}" in root.tag else ""
        if root.tag.endswith("sitemapindex"):
            for loc in root.findall(f"{ns}sitemap/{ns}loc"):
                if loc.text:
                    queue.append(loc.text.strip())
        elif root.tag.endswith("urlset"):
            for loc in root.findall(f"{ns}url/{ns}loc"):
                if loc.text:
                    urls.append(loc.text.strip())

    # Yoast emits some URLs (e.g. homepage) in multiple child sitemaps. Dedup, preserve order.
    return list(dict.fromkeys(urls))


class _RedirectTracker(urllib.request.HTTPRedirectHandler):
    """Records the redirect chain followed by urllib for a single request."""

    def __init__(self) -> None:
        super().__init__()
        self.chain: list[dict] = []

    def http_error_301(self, req, fp, code, msg, headers):
        self.chain.append({
            "from": req.get_full_url(),
            "to": headers.get("Location", ""),
            "status": code,
        })
        return super().http_error_301(req, fp, code, msg, headers)

    http_error_302 = http_error_303 = http_error_307 = http_error_308 = http_error_301


def fetch_page(url: str, user_agent: str, timeout: int = 30) -> dict:
    """Fetch one URL. Returns dict with status, final_url, body, redirects, content_type, fetched_at."""
    tracker = _RedirectTracker()
    opener = urllib.request.build_opener(tracker)
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with opener.open(req, timeout=timeout) as resp:
            return {
                "url": url,
                "final_url": resp.geturl(),
                "status": resp.status,
                "redirects": tracker.chain,
                "body": resp.read(),
                "content_type": resp.headers.get("Content-Type", ""),
                "fetched_at": utc_now(),
            }
    except urllib.error.HTTPError as e:
        return {
            "url": url,
            "final_url": getattr(e, "url", url),
            "status": e.code,
            "redirects": tracker.chain,
            "body": b"",
            "content_type": "",
            "fetched_at": utc_now(),
            "error": str(e),
        }
    except Exception as e:
        return {
            "url": url,
            "final_url": url,
            "status": 0,
            "redirects": tracker.chain,
            "body": b"",
            "content_type": "",
            "fetched_at": utc_now(),
            "error": str(e),
        }


def parse_page(url: str, html_bytes: bytes, site_host: str) -> dict:
    """Extract structured SEO fields from a fetched HTML body.

    site_host classifies links: same host = internal, other = outbound.
    Word count is taken from <article> if present, else <main>, else <body>.
    """
    if not html_bytes:
        return _empty_parse()

    soup = BeautifulSoup(html_bytes, "html.parser")

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    meta = soup.find("meta", attrs={"name": "description"})
    meta_desc = meta.get("content", "").strip() if meta else ""

    canonical_tag = soup.find("link", rel="canonical")
    canonical = canonical_tag.get("href", "").strip() if canonical_tag else ""

    h1s = [h.get_text(strip=True) for h in soup.find_all("h1")]

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    content_root = soup.find("article") or soup.find("main") or soup.body or soup
    text = content_root.get_text(separator=" ", strip=True)
    word_count = len(text.split())

    internal_links: list[str] = []
    outbound_links: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
            continue
        absolute = urllib.parse.urljoin(url, href)
        host = urllib.parse.urlparse(absolute).netloc
        if host == site_host or host == "":
            internal_links.append(absolute)
        else:
            outbound_links.append(absolute)

    images_without_alt = sum(1 for img in soup.find_all("img") if not img.get("alt"))

    return {
        "title": title,
        "meta_description": meta_desc,
        "canonical": canonical,
        "h1": h1s,
        "word_count": word_count,
        "text": text,
        "internal_links": internal_links,
        "outbound_links": outbound_links,
        "images_without_alt": images_without_alt,
    }


def _empty_parse() -> dict:
    return {
        "title": "",
        "meta_description": "",
        "canonical": "",
        "h1": [],
        "word_count": 0,
        "text": "",
        "internal_links": [],
        "outbound_links": [],
        "images_without_alt": 0,
    }

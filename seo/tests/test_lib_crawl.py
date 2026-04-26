from unittest.mock import patch

from lib.crawl import RateLimiter, parse_page


# ---------------------------------------------------------------------------
# parse_page
# ---------------------------------------------------------------------------

_BASE = "https://hybridautopart.com/blog-en/post/"
_HOST = "hybridautopart.com"


def test_parse_page_empty_body():
    out = parse_page(_BASE, b"", _HOST)
    assert out["title"] == ""
    assert out["word_count"] == 0
    assert out["internal_links"] == []


def test_parse_page_extracts_title_meta_canonical():
    html = b"""
    <html><head>
      <title>  Toyota PSD Explained  </title>
      <meta name="description" content="A guide to Toyota's Power Split Device.">
      <link rel="canonical" href="https://hybridautopart.com/blog-en/psd/">
    </head><body><h1>Power Split Device</h1></body></html>
    """
    out = parse_page(_BASE, html, _HOST)
    assert out["title"] == "Toyota PSD Explained"
    assert out["meta_description"] == "A guide to Toyota's Power Split Device."
    assert out["canonical"] == "https://hybridautopart.com/blog-en/psd/"
    assert out["h1"] == ["Power Split Device"]


def test_parse_page_word_count_uses_article_when_present():
    html = b"""
    <html><body>
      <nav>nav nav nav nav nav nav</nav>
      <article>one two three four five six seven eight</article>
      <footer>footer footer footer</footer>
    </body></html>
    """
    out = parse_page(_BASE, html, _HOST)
    assert out["word_count"] == 8


def test_parse_page_word_count_falls_back_to_body():
    html = b"<html><body>alpha beta gamma</body></html>"
    out = parse_page(_BASE, html, _HOST)
    assert out["word_count"] == 3


def test_parse_page_classifies_internal_vs_outbound_links():
    html = b"""
    <html><body>
      <a href="/blog-en/other/">internal relative</a>
      <a href="https://hybridautopart.com/blog-en/x/">internal absolute</a>
      <a href="https://wikipedia.org/wiki/Prius">outbound</a>
      <a href="#anchor">skipped</a>
      <a href="mailto:x@y.com">skipped</a>
    </body></html>
    """
    out = parse_page(_BASE, html, _HOST)
    assert "https://hybridautopart.com/blog-en/other/" in out["internal_links"]
    assert "https://hybridautopart.com/blog-en/x/" in out["internal_links"]
    assert "https://wikipedia.org/wiki/Prius" in out["outbound_links"]
    assert all(not link.startswith("#") for link in out["internal_links"] + out["outbound_links"])


def test_parse_page_strips_script_and_style_from_word_count():
    html = b"""
    <html><body>
      <script>var a = 'should not count';</script>
      <style>.x { color: red; should not count }</style>
      <article>real real real</article>
    </body></html>
    """
    out = parse_page(_BASE, html, _HOST)
    assert out["word_count"] == 3


def test_parse_page_counts_images_without_alt():
    html = b"""
    <html><body>
      <img src="a.jpg" alt="ok">
      <img src="b.jpg">
      <img src="c.jpg" alt="">
    </body></html>
    """
    out = parse_page(_BASE, html, _HOST)
    # `alt=""` is falsy -> counted as missing alt, matching SEO convention
    assert out["images_without_alt"] == 2


def test_parse_page_handles_missing_meta_and_canonical():
    html = b"<html><head><title>t</title></head><body>x</body></html>"
    out = parse_page(_BASE, html, _HOST)
    assert out["meta_description"] == ""
    assert out["canonical"] == ""


# ---------------------------------------------------------------------------
# RateLimiter
# ---------------------------------------------------------------------------

def test_rate_limiter_first_call_does_not_sleep():
    rl = RateLimiter(delay_s=0.5)
    with patch("time.sleep") as sleep_mock:
        rl.wait()
    sleep_mock.assert_not_called()


def test_rate_limiter_sleeps_when_called_too_soon():
    rl = RateLimiter(delay_s=0.5, jitter_s=0.0)
    # wait #1: monotonic() for elapsed-check, then monotonic() to stamp _last_at
    # wait #2: monotonic() for elapsed-check (0.1s later → must sleep), then stamp
    times = iter([100.0, 100.0, 100.1, 100.5])

    with patch("time.monotonic", side_effect=lambda: next(times)), \
         patch("time.sleep") as sleep_mock:
        rl.wait()
        rl.wait()

    sleep_mock.assert_called_once()
    arg = sleep_mock.call_args[0][0]
    assert 0.39 < arg <= 0.5  # ~0.4s remaining (0.5 - 0.1)

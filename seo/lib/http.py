import random
import time
import urllib.error

from lib.io import log


def with_retry(fn, max_retries: int, label: str):
    """Call fn(), retrying with exponential backoff. Raises on final failure."""
    attempt = 0
    last_error = None
    while attempt <= max_retries:
        try:
            return fn()
        except urllib.error.HTTPError as e:
            last_error = e
            if e.code in (401, 403):
                raise
            wait = (2 ** attempt) + random.uniform(0, 1)
            log(f"  RETRY [{attempt + 1}/{max_retries}] {label} — HTTP {e.code}, waiting {wait:.1f}s")
        except Exception as e:
            last_error = e
            wait = (2 ** attempt) + random.uniform(0, 1)
            log(f"  RETRY [{attempt + 1}/{max_retries}] {label} — {type(e).__name__}: {e}, waiting {wait:.1f}s")
        attempt += 1
        if attempt <= max_retries:
            time.sleep(wait)
        else:
            log(f"  all {max_retries + 1} attempts failed for: {label}")
    raise last_error


def error_code_for(e: Exception) -> str:
    if isinstance(e, urllib.error.HTTPError):
        return f"HTTP_{e.code}"
    if isinstance(e, urllib.error.URLError):
        return "URL_ERROR"
    if isinstance(e, TimeoutError):
        return "TIMEOUT"
    if isinstance(e, FileNotFoundError):
        return "FILE_NOT_FOUND"
    return "ERR"

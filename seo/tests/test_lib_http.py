import urllib.error
import urllib.request
import pytest
from unittest.mock import patch
from lib.http import error_code_for, with_retry


# ---------------------------------------------------------------------------
# error_code_for
# ---------------------------------------------------------------------------

def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(url="http://x", code=code, msg="", hdrs=None, fp=None)


def test_error_code_http():
    assert error_code_for(_http_error(429)) == "HTTP_429"
    assert error_code_for(_http_error(500)) == "HTTP_500"


def test_error_code_url_error():
    e = urllib.error.URLError(reason="name resolution failed")
    assert error_code_for(e) == "URL_ERROR"


def test_error_code_timeout():
    assert error_code_for(TimeoutError()) == "TIMEOUT"


def test_error_code_file_not_found():
    assert error_code_for(FileNotFoundError()) == "FILE_NOT_FOUND"


def test_error_code_generic():
    assert error_code_for(RuntimeError("oops")) == "ERR"


# ---------------------------------------------------------------------------
# with_retry
# ---------------------------------------------------------------------------

def test_with_retry_succeeds_first_try():
    fn = lambda: 42
    assert with_retry(fn, max_retries=3, label="t") == 42


def test_with_retry_succeeds_after_failures():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("transient")
        return "ok"

    with patch("time.sleep"):
        result = with_retry(fn, max_retries=3, label="t")
    assert result == "ok"
    assert calls["n"] == 3


def test_with_retry_raises_after_max_retries():
    fn = lambda: (_ for _ in ()).throw(RuntimeError("always"))

    with patch("time.sleep"):
        with pytest.raises(RuntimeError, match="always"):
            with_retry(fn, max_retries=2, label="t")


def test_with_retry_raises_immediately_on_401():
    def fn():
        raise _http_error(401)

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        with_retry(fn, max_retries=3, label="t")
    assert exc_info.value.code == 401


def test_with_retry_raises_immediately_on_403():
    def fn():
        raise _http_error(403)

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        with_retry(fn, max_retries=3, label="t")
    assert exc_info.value.code == 403


def test_with_retry_retries_on_500():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        raise _http_error(500)

    with patch("time.sleep"):
        with pytest.raises(urllib.error.HTTPError):
            with_retry(fn, max_retries=2, label="t")

    assert calls["n"] == 3  # initial + 2 retries


def test_with_retry_zero_retries_raises_immediately():
    fn = lambda: (_ for _ in ()).throw(RuntimeError("x"))

    with patch("time.sleep"):
        with pytest.raises(RuntimeError):
            with_retry(fn, max_retries=0, label="t")

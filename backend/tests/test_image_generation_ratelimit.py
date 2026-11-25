"""
test_image_generation_ratelimit.py
───────────────────────────────────
Unit tests for Pollinations rate-limit / promo-card detection in
services/image_generation.py.  All HTTP calls are mocked.

Run with:
    ..\\.venv2\\Scripts\\python.exe -m pytest tests/test_image_generation_ratelimit.py -v
"""
import os
import sys
import asyncio
import unittest.mock as mock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def run(coro):
    return asyncio.run(coro)


# ── Fake httpx response ───────────────────────────────────────────────────────

class FakeHttpxResponse:
    def __init__(self, status_code: int, content: bytes, content_type: str = "image/png"):
        self.status_code = status_code
        self.content = content
        self.headers = {"content-type": content_type}

    def raise_for_status(self):
        pass


def _make_client_mock(response: FakeHttpxResponse):
    client = mock.AsyncMock()
    client.__aenter__ = mock.AsyncMock(return_value=client)
    client.__aexit__ = mock.AsyncMock(return_value=False)
    client.get = mock.AsyncMock(return_value=response)
    return client


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestPollinationsRatelimit:

    def test_valid_image_returns_success(self, tmp_path):
        """200 + image/png + big body → success."""
        from services.image_generation import generate_ai_image

        fake_body = b"\x89PNG\r\n\x1a\n" + b"\x00" * 5000  # > 3 kB
        resp = FakeHttpxResponse(200, fake_body, "image/png")

        with mock.patch("httpx.AsyncClient", return_value=_make_client_mock(resp)):
            result = run(generate_ai_image("a mountain lake"))

        assert result["success"] is True
        assert result["url"] is not None

    def test_html_promo_response_treated_as_failure(self, tmp_path):
        """200 + text/html content-type → rate-limit failure, not success."""
        from services.image_generation import generate_ai_image

        html_body = b"<html><body>Free limit reached. Upgrade to continue.</body></html>"
        resp = FakeHttpxResponse(200, html_body, "text/html; charset=utf-8")

        with mock.patch("httpx.AsyncClient", return_value=_make_client_mock(resp)):
            result = run(generate_ai_image("a sunny beach"))

        assert result["success"] is False
        assert result["url"] is None
        assert "rate-limit" in result["error"].lower() or "rate" in result["error"].lower()

    def test_tiny_image_treated_as_failure(self, tmp_path):
        """200 + image/png but < 3000 bytes → rate-limit promo card rejected."""
        from services.image_generation import generate_ai_image

        tiny_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # < 3 kB
        resp = FakeHttpxResponse(200, tiny_png, "image/png")

        with mock.patch("httpx.AsyncClient", return_value=_make_client_mock(resp)):
            result = run(generate_ai_image("a forest scene"))

        assert result["success"] is False
        assert result["url"] is None
        assert "rate" in result["error"].lower()

    def test_non_200_status_treated_as_failure(self, tmp_path):
        """HTTP 429 → failure with status message."""
        from services.image_generation import generate_ai_image

        resp = FakeHttpxResponse(429, b"Too Many Requests", "text/plain")

        with mock.patch("httpx.AsyncClient", return_value=_make_client_mock(resp)):
            result = run(generate_ai_image("a city skyline"))

        assert result["success"] is False
        assert result["url"] is None

    def test_timeout_returns_error(self):
        """Timeout → helpful error message, not exception."""
        import httpx
        from services.image_generation import generate_ai_image

        client_mock = mock.AsyncMock()
        client_mock.__aenter__ = mock.AsyncMock(return_value=client_mock)
        client_mock.__aexit__ = mock.AsyncMock(return_value=False)
        client_mock.get = mock.AsyncMock(side_effect=httpx.TimeoutException("timed out"))

        with mock.patch("httpx.AsyncClient", return_value=client_mock):
            result = run(generate_ai_image("a robot"))

        assert result["success"] is False
        assert "timeout" in result["error"].lower() or "timed" in result["error"].lower()

    def test_empty_prompt_returns_error(self):
        """Empty prompt → error without making any HTTP call."""
        from services.image_generation import generate_ai_image

        with mock.patch("httpx.AsyncClient") as client_cls:
            result = run(generate_ai_image(""))

        assert result["success"] is False
        client_cls.assert_not_called()

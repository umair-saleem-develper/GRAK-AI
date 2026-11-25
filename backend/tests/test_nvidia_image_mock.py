"""
test_nvidia_image_mock.py
─────────────────────────
Validates the NVIDIA image service logic WITHOUT using any real NVIDIA quota.
All HTTP calls are mocked. Run with:
    ..\.venv2\Scripts\python.exe -m pytest tests/test_nvidia_image_mock.py -v
"""
import os, sys, pytest, asyncio, unittest.mock as mock

# Inject the backend root so imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ── Fixture: patch env and pollinations before importing the module ────────────
@pytest.fixture(autouse=True)
def patch_env_and_pollinations(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY2", "nvapi-primarykey234567890")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-testkey1234567890")
    monkeypatch.setenv("NVIDIA_IMAGE_MODEL", "")   # must NOT interfere

    # Patch pollinations so we never hit the internet
    async def fake_pollinations(prompt, **kwargs):
        return {"success": True, "url": "https://pollinations.ai/fake.jpg",
                "enhanced_prompt": prompt}

    import services.image_generation as ig
    monkeypatch.setattr(ig, "generate_ai_image", fake_pollinations)


# ── Helper ────────────────────────────────────────────────────────────────────
def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ─────────────────────────────────────────────────────────────────────────────
# Prompt cleaning tests (no HTTP, pure logic)
# ─────────────────────────────────────────────────────────────────────────────
class TestCleanPrompt:
    def setup_method(self):
        from services.nvidia_image import _clean_prompt
        self.clean = _clean_prompt

    def test_strips_like_a(self):
        result = self.clean("like a sweet cat")
        assert "cat" in result
        assert "like" not in result.lower()

    def test_strips_create_image(self):
        result = self.clean("create image of a dog")
        assert "dog" in result
        assert "create" not in result.lower()

    def test_strips_generate_image_of(self):
        result = self.clean("generate image of sunset")
        assert "sunset" in result

    def test_short_subject_expanded(self):
        result = self.clean("a sweet cat")
        # Should have quality keywords appended
        assert "photo" in result.lower() or "quality" in result.lower()

    def test_long_prompt_unchanged_subject(self):
        long = "a majestic lion standing on a rock at sunset in the savanna during golden hour"
        result = self.clean(long)
        assert "lion" in result

    def test_no_people_replacement(self):
        result = self.clean("like a sweet cat")
        # The word 'human' or 'person' should NOT appear
        assert "human" not in result.lower()
        assert "person" not in result.lower()
        assert "man" not in result.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Key detection tests
# ─────────────────────────────────────────────────────────────────────────────
class TestGetKey:
    def test_prefers_nvidia_api_key2(self, monkeypatch):
        monkeypatch.setenv("NVIDIA_API_KEY2", "nvapi-key2-primary")
        monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-key1-fallback")
        from importlib import reload
        import services.nvidia_image as m
        reload(m)
        assert m._get_key() == "nvapi-key2-primary"
        assert m._get_key_candidates() == [
            ("NVIDIA_API_KEY2", "nvapi-key2-primary"),
            ("NVIDIA_API_KEY", "nvapi-key1-fallback"),
        ]

    def test_reads_nvidia_api_key_when_key2_missing(self, monkeypatch):
        monkeypatch.setenv("NVIDIA_API_KEY2", "")
        monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-goodkey")
        from importlib import reload
        import services.nvidia_image as m
        reload(m)
        assert m._get_key() == "nvapi-goodkey"

    def test_legacy_fallback_key(self, monkeypatch):
        monkeypatch.setenv("NVIDIA_API_KEY2", "")
        monkeypatch.setenv("NVIDIA_API_KEY", "")
        monkeypatch.setenv("NVIDIA_IMAGE_MODEL", "nvapi-legacykey")
        from importlib import reload
        import services.nvidia_image as m
        reload(m)
        assert m._get_key() == "nvapi-legacykey"

    def test_legacy_key_with_equals_prefix(self, monkeypatch):
        monkeypatch.setenv("NVIDIA_API_KEY2", "")
        monkeypatch.setenv("NVIDIA_API_KEY", "")
        monkeypatch.setenv("NVIDIA_IMAGE_MODEL", "=nvapi-legacykey2")
        from importlib import reload
        import services.nvidia_image as m
        reload(m)
        assert m._get_key() == "nvapi-legacykey2"


# ─────────────────────────────────────────────────────────────────────────────
# HTTP mock tests
# ─────────────────────────────────────────────────────────────────────────────
import base64, json

FAKE_PNG = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100).decode()

class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self): return self._body
    @property
    def text(self): return json.dumps(self._body)
    def raise_for_status(self): pass


class TestGenerateNvidiaImage:

    def _make_httpx_mock(self, status, body):
        fake_resp = FakeResponse(status, body)
        client_mock = mock.AsyncMock()
        client_mock.__aenter__ = mock.AsyncMock(return_value=client_mock)
        client_mock.__aexit__  = mock.AsyncMock(return_value=False)
        client_mock.post = mock.AsyncMock(return_value=fake_resp)
        return client_mock

    def test_nvidia_200_artifacts_base64(self, monkeypatch, tmp_path):
        """NVIDIA returns artifacts[0].base64 → provider=nvidia, no fallback."""
        body = {"artifacts": [{"base64": FAKE_PNG}]}
        client_mock = self._make_httpx_mock(200, body)
        monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-testkey1234567890")

        import services.nvidia_image as m
        monkeypatch.setattr(m, "DOWNLOADS_DIR", str(tmp_path))

        with mock.patch("httpx.AsyncClient", return_value=client_mock):
            result = run(m.generate_nvidia_image("like a sweet cat"))

        assert result["success"] is True
        assert result["provider"] == "nvidia"
        assert result["fallback"] is False
        assert "cat" in result["enhanced_prompt"].lower()
        assert result["url"].startswith("/api/images/nvidia_")

    def test_nvidia_429_falls_back_to_pollinations(self, monkeypatch, tmp_path):
        """NVIDIA returns 429 → WARNING logged → fallback to Pollinations."""
        body = {"error": "rate limit"}
        client_mock = self._make_httpx_mock(429, body)
        monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-testkey1234567890")

        import services.nvidia_image as m
        monkeypatch.setattr(m, "DOWNLOADS_DIR", str(tmp_path))

        with mock.patch("httpx.AsyncClient", return_value=client_mock):
            with mock.patch.object(m.logger, "warning") as warn_mock:
                result = run(m.generate_nvidia_image("a dog"))

        assert result["success"] is True
        assert result["provider"] == "pollinations"
        assert result["fallback"] is True
        # Warning must have been logged
        logged_msgs = " ".join(str(c) for c in warn_mock.call_args_list)
        assert "FALLBACK" in logged_msgs

    def test_nvidia_timeout_falls_back(self, monkeypatch, tmp_path):
        """NVIDIA timeout → fallback to Pollinations with WARNING."""
        import httpx
        monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-testkey1234567890")

        import services.nvidia_image as m
        monkeypatch.setattr(m, "DOWNLOADS_DIR", str(tmp_path))

        async def raise_timeout(*a, **kw):
            raise httpx.TimeoutException("timed out")

        client_mock = mock.AsyncMock()
        client_mock.__aenter__ = mock.AsyncMock(return_value=client_mock)
        client_mock.__aexit__  = mock.AsyncMock(return_value=False)
        client_mock.post = raise_timeout

        with mock.patch("httpx.AsyncClient", return_value=client_mock):
            with mock.patch.object(m.logger, "warning") as warn_mock:
                result = run(m.generate_nvidia_image("mountain"))

        assert result["provider"] == "pollinations"
        assert result["fallback"] is True
        warn_msgs = " ".join(str(c) for c in warn_mock.call_args_list)
        assert "FALLBACK" in warn_msgs

    def test_missing_key_falls_back(self, monkeypatch, tmp_path):
        """No API key → warning + fallback to Pollinations."""
        monkeypatch.setenv("NVIDIA_API_KEY2", "")
        monkeypatch.setenv("NVIDIA_API_KEY", "")
        monkeypatch.setenv("NVIDIA_IMAGE_MODEL", "")

        import services.nvidia_image as m
        monkeypatch.setattr(m, "DOWNLOADS_DIR", str(tmp_path))

        result = run(m.generate_nvidia_image("a cat"))
        assert result["provider"] == "pollinations"
        assert result["fallback"] is True

    def test_empty_prompt_returns_error(self, monkeypatch, tmp_path):
        import services.nvidia_image as m
        result = run(m.generate_nvidia_image(""))
        assert result["success"] is False
        assert result["provider"] == "none"

    def test_seed_and_mode_not_in_payload(self, monkeypatch, tmp_path):
        """Payload must NOT contain 'seed' (422 extra_forbidden) or 'mode' keys."""
        body = {"artifacts": [{"base64": FAKE_PNG}]}
        client_mock = self._make_httpx_mock(200, body)
        monkeypatch.setenv("NVIDIA_API_KEY2", "nvapi-testkey2")
        monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-testkey1")

        import services.nvidia_image as m
        monkeypatch.setattr(m, "DOWNLOADS_DIR", str(tmp_path))

        captured_payload = {}
        captured_headers = {}

        async def spy_post(url, headers, json, **kwargs):
            captured_payload.update(json)
            captured_headers.update(headers)
            return FakeResponse(200, body)

        client_mock.post = spy_post
        with mock.patch("httpx.AsyncClient", return_value=client_mock):
            result = run(m.generate_nvidia_image("a bird"))

        assert result["success"] is True
        assert result["provider"] == "nvidia"
        assert result["model"] == "black-forest-labs/flux-3-image-klein"
        assert captured_headers.get("Authorization") == "Bearer nvapi-testkey2"
        assert "mode" not in captured_payload, "Payload must not contain 'mode' key"
        assert "seed" not in captured_payload, "Payload must not contain 'seed' key (causes HTTP 422 extra_forbidden)"
        assert "width" in captured_payload
        assert "height" in captured_payload
        assert "steps" in captured_payload
        assert "prompt" in captured_payload

    def test_422_retries_prompt_only_and_falls_back_on_persistent_error(self, monkeypatch, tmp_path):
        """HTTP 422 triggers prompt-only retry; if NVIDIA_API_KEY2 and NVIDIA_API_KEY fail, falls back to Pollinations."""
        monkeypatch.setenv("NVIDIA_API_KEY2", "nvapi-key2")
        monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-key1")

        import services.nvidia_image as m
        monkeypatch.setattr(m, "DOWNLOADS_DIR", str(tmp_path))

        calls = []

        async def spy_post(url, headers, json, **kwargs):
            calls.append((url, headers["Authorization"], dict(json)))
            if headers["Authorization"] == "Bearer nvapi-key2" and len(json) > 1:
                return FakeResponse(422, {"detail": [{"type": "extra_forbidden"}]})
            if headers["Authorization"] == "Bearer nvapi-key2" and list(json.keys()) == ["prompt"]:
                return FakeResponse(200, {"artifacts": [{"base64": FAKE_PNG}]})
            return FakeResponse(500, {"error": "unexpected"})

        client_mock = mock.AsyncMock()
        client_mock.__aenter__ = mock.AsyncMock(return_value=client_mock)
        client_mock.__aexit__ = mock.AsyncMock(return_value=False)
        client_mock.post = spy_post

        with mock.patch("httpx.AsyncClient", return_value=client_mock):
            result = run(m.generate_nvidia_image("sunset"))

        assert result["success"] is True
        assert result["provider"] == "nvidia"
        assert len(calls) == 2
        assert list(calls[1][2].keys()) == ["prompt"]

    # ─────────────────────────────────────────────────────────────────────────
    # CONTENT_FILTERED tests
    # ─────────────────────────────────────────────────────────────────────────

    def test_content_filtered_retries_with_sanitized_prompt(self, monkeypatch, tmp_path):
        """NVIDIA returns CONTENT_FILTERED → auto-sanitize → retry succeeds."""
        monkeypatch.setenv("NVIDIA_API_KEY2", "nvapi-key2")
        monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-key1")

        import services.nvidia_image as m
        monkeypatch.setattr(m, "DOWNLOADS_DIR", str(tmp_path))

        call_prompts = []

        async def spy_post(url, headers, json, **kwargs):
            call_prompts.append(json.get("prompt", ""))
            if len(call_prompts) == 1:
                # First call: return CONTENT_FILTERED
                return FakeResponse(200, {"artifacts": [{"finishReason": "CONTENT_FILTERED", "base64": ""}]})
            # Second call (sanitized prompt): succeed
            return FakeResponse(200, {"artifacts": [{"base64": FAKE_PNG}]})

        client_mock = mock.AsyncMock()
        client_mock.__aenter__ = mock.AsyncMock(return_value=client_mock)
        client_mock.__aexit__ = mock.AsyncMock(return_value=False)
        client_mock.post = spy_post

        with mock.patch("httpx.AsyncClient", return_value=client_mock):
            result = run(m.generate_nvidia_image("violent blood explosion"))

        assert result["success"] is True
        assert result["provider"] == "nvidia"
        assert len(call_prompts) == 2, "Should have called NVIDIA exactly twice"
        # Second prompt must differ from first (sanitized)
        assert call_prompts[0] != call_prompts[1], "Retry prompt must be sanitized"

    def test_content_filtered_persistent_falls_back_to_pollinations(self, monkeypatch, tmp_path):
        """CONTENT_FILTERED on both original AND sanitized prompt → fallback to Pollinations."""
        monkeypatch.setenv("NVIDIA_API_KEY2", "nvapi-key2")
        monkeypatch.setenv("NVIDIA_API_KEY", "")  # only one key

        import services.nvidia_image as m
        monkeypatch.setattr(m, "DOWNLOADS_DIR", str(tmp_path))

        async def always_filtered(url, headers, json, **kwargs):
            return FakeResponse(200, {"artifacts": [{"finishReason": "CONTENT_FILTERED", "base64": ""}]})

        client_mock = mock.AsyncMock()
        client_mock.__aenter__ = mock.AsyncMock(return_value=client_mock)
        client_mock.__aexit__ = mock.AsyncMock(return_value=False)
        client_mock.post = always_filtered

        with mock.patch("httpx.AsyncClient", return_value=client_mock):
            result = run(m.generate_nvidia_image("violent blood scene"))

        assert result["success"] is True           # Pollinations fake always succeeds
        assert result["provider"] == "pollinations"
        assert result["fallback"] is True

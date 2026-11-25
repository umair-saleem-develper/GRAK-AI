"""
test_image_studio.py
────────────────────
Unit & mock verification for Grak AI Image Studio:
  1. 100+ line detailed prompt routed to Gemini Native Image without truncation
  2. Gemini model fallback (gemini-2.5-flash-image -> gemini-2.0-flash-exp-image-generation)
  3. Multi-turn iterative image editing (v1 -> v2 -> v3) sending both image bytes & edit instruction
  4. Conversational follow-up edit detection + block prompt sanitization
  5. Gemini 429 quota fallback -> LLM condensation (<350 words) -> NVIDIA flux-3-image-klein
"""

import asyncio
import base64
import os
import sys
import types as pytypes
import unittest.mock as mock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

FAKE_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 128


def run(coro):
    return asyncio.run(coro)


def _make_100_line_prompt() -> str:
    lines = [
        f"Line {i:03d}: ultra-detailed cyberpunk rain-soaked Tokyo alley with neon kanji reflections, wet cobblestones, volumetric mist, and 35mm cinematic bokeh."
        for i in range(1, 106)
    ]
    return "\n".join(lines)


def _make_fake_gemini_response(img_bytes=FAKE_PNG_BYTES, mime="image/png", text="Generated"):
    inline = pytypes.SimpleNamespace(data=img_bytes, mime_type=mime)
    part_img = pytypes.SimpleNamespace(inline_data=inline, text=None)
    part_txt = pytypes.SimpleNamespace(inline_data=None, text=text)
    content = pytypes.SimpleNamespace(parts=[part_txt, part_img])
    cand = pytypes.SimpleNamespace(content=content)
    return pytypes.SimpleNamespace(candidates=[cand])


class TestLongPromptAndFollowupDetection:
    def test_100_line_prompt_detected_as_long(self):
        from services.image_studio import is_long_detailed_prompt
        prompt = _make_100_line_prompt()
        assert len(prompt.splitlines()) == 105
        assert is_long_detailed_prompt(prompt) is True

    def test_short_prompt_not_long(self):
        from services.image_studio import is_long_detailed_prompt
        assert is_long_detailed_prompt("a golden retriever puppy in a park") is False

    def test_sanitize_block_prompt_safe_for_card_parser(self):
        from services.image_studio import sanitize_block_prompt
        raw = "Line one :::bad:::\nLine two with details\n" + ("word " * 100)
        safe = sanitize_block_prompt(raw)
        assert "\n" not in safe
        assert ":::" not in safe
        assert len(safe) <= 240

    def test_followup_edit_detection_after_generated_image(self):
        from services.image_studio import is_followup_edit_request
        history = [
            {"role": "user", "content": "Create a portrait of a boy in a red shirt"},
            {
                "role": "assistant",
                "content": ":::generated-image\nimage: /api/images/nvidia_v1.png\nprompt: a portrait of a boy in a red shirt\n:::\n",
            },
        ]
        res1 = is_followup_edit_request("make the shirt blue", history, mode=None)
        assert res1 is not None
        assert res1[0] == "/api/images/nvidia_v1.png"

        res2 = is_followup_edit_request("change the background to sunset", history, mode="create_image")
        assert res2 is not None
        assert res2[0] == "/api/images/nvidia_v1.png"

        res3 = is_followup_edit_request("add text GRAK AI on top", history, mode=None)
        assert res3 is not None

        # Explicit brand new creation should NOT hijack as edit
        res_new = is_followup_edit_request("create a brand new image of a futuristic rocket", history, mode="create_image")
        assert res_new is None


class TestGeminiNativeImage:
    def test_100_line_prompt_untruncated_and_saved(self, monkeypatch, tmp_path):
        import services.gemini_image as gi
        monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestFakeKey12345")
        monkeypatch.setattr(gi, "DOWNLOADS_DIR", str(tmp_path))

        prompt_100 = _make_100_line_prompt()
        captured_calls = []

        async def fake_generate_content(model, contents, config):
            captured_calls.append({"model": model, "contents": contents, "config": config})
            return _make_fake_gemini_response()

        fake_client = pytypes.SimpleNamespace(
            aio=pytypes.SimpleNamespace(
                models=pytypes.SimpleNamespace(generate_content=fake_generate_content)
            )
        )

        with mock.patch("google.genai.Client", return_value=fake_client):
            result = run(gi.generate_gemini_image(prompt_100))

        assert result["success"] is True
        assert result["provider"] == "gemini"
        assert result["model"] == "gemini-2.5-flash-image"
        assert result["fallback"] is False
        assert result["url"].startswith("/api/images/gemini_")
        # Full 105-line prompt preserved verbatim without truncation
        sent_text = captured_calls[0]["contents"][0].text
        assert sent_text == prompt_100
        assert "Line 105:" in sent_text
        saved_name = os.path.basename(result["url"])
        assert os.path.isfile(os.path.join(tmp_path, saved_name))

    def test_gemini_model_fallback_to_20_exp(self, monkeypatch, tmp_path):
        import services.gemini_image as gi
        monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestFakeKey12345")
        monkeypatch.setattr(gi, "DOWNLOADS_DIR", str(tmp_path))

        models_tried = []

        async def fake_generate_content(model, contents, config):
            models_tried.append(model)
            if model == "gemini-2.5-flash-image":
                raise RuntimeError("404 NOT_FOUND")
            return _make_fake_gemini_response()

        fake_client = pytypes.SimpleNamespace(
            aio=pytypes.SimpleNamespace(
                models=pytypes.SimpleNamespace(generate_content=fake_generate_content)
            )
        )

        with mock.patch("google.genai.Client", return_value=fake_client):
            result = run(gi.generate_gemini_image("a cozy cyberpunk cafe"))

        assert models_tried == ["gemini-2.5-flash-image", "gemini-2.0-flash-exp-image-generation"]
        assert result["success"] is True
        assert result["model"] == "gemini-2.0-flash-exp-image-generation"
        assert result["fallback"] is True


class TestIterativeEditingAndFallback:
    def test_iterative_edit_sends_source_image_and_instruction(self, monkeypatch, tmp_path):
        import services.image_studio as studio
        import services.gemini_image as gi

        monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestFakeKey12345")
        monkeypatch.setattr(studio, "DOWNLOADS_DIR", str(tmp_path))
        monkeypatch.setattr(gi, "DOWNLOADS_DIR", str(tmp_path))

        # Write v1 image locally
        v1_path = os.path.join(tmp_path, "nvidia_v1test.png")
        with open(v1_path, "wb") as f:
            f.write(FAKE_PNG_BYTES)

        captured_parts = []

        async def fake_generate_content(model, contents, config):
            captured_parts.extend(contents)
            return _make_fake_gemini_response(img_bytes=FAKE_PNG_BYTES + b"v2")

        fake_client = pytypes.SimpleNamespace(
            aio=pytypes.SimpleNamespace(
                models=pytypes.SimpleNamespace(generate_content=fake_generate_content)
            )
        )

        with mock.patch("google.genai.Client", return_value=fake_client):
            res_v2 = run(
                studio.generate_or_edit_image(
                    prompt="change the background to sunset",
                    source_image_ref="/api/images/nvidia_v1test.png",
                    prior_prompt="a cat sitting on grass",
                )
            )

        assert res_v2["success"] is True
        assert res_v2["provider"] == "gemini"
        assert res_v2["edited"] is True
        assert res_v2["url"].startswith("/api/images/gemini_")
        # Both image bytes and edit instruction text were sent to Gemini
        assert len(captured_parts) == 2
        assert captured_parts[0].inline_data.data == FAKE_PNG_BYTES
        assert "change the background to sunset" in captured_parts[1].text

        # Sequential v2 -> v3 edit
        captured_parts.clear()
        with mock.patch("google.genai.Client", return_value=fake_client):
            res_v3 = run(
                studio.generate_or_edit_image(
                    prompt="add text GRAK AI on top",
                    source_image_ref=res_v2["url"],
                    prior_prompt="change the background to sunset",
                )
            )
        assert res_v3["success"] is True
        assert res_v3["edited"] is True
        assert captured_parts[0].inline_data.data == FAKE_PNG_BYTES + b"v2"
        assert "add text GRAK AI on top" in captured_parts[1].text

    def test_gemini_quota_fallback_condenses_long_prompt_for_nvidia(self, monkeypatch, tmp_path):
        import services.image_studio as studio

        prompt_100 = _make_100_line_prompt()
        assert len(prompt_100.split()) > 1000

        async def fake_gemini_fail(*args, **kwargs):
            return {
                "success": False,
                "error": "429 RESOURCE_EXHAUSTED quota exceeded",
                "url": None,
                "provider": "none",
                "model": "none",
            }

        nvidia_received = {}

        async def fake_nvidia(prompt, width=1024, height=1024, use_fallback_on_error=True):
            nvidia_received["prompt"] = prompt
            return {
                "success": True,
                "url": "/api/images/nvidia_condensed.png",
                "prompt": prompt,
                "enhanced_prompt": prompt,
                "provider": "nvidia",
                "model": "black-forest-labs/flux-3-image-klein",
                "fallback": False,
            }

        async def fake_gateway_chat(self, messages, apply_identity=False):
            return pytypes.SimpleNamespace(
                content="Cyberpunk rain-soaked Tokyo alley at night with neon kanji reflections on wet cobblestones, volumetric mist, 35mm cinematic bokeh",
                provider="groq",
                model="openai/gpt-oss-120b",
            )

        monkeypatch.setattr(studio, "generate_gemini_image", fake_gemini_fail)
        monkeypatch.setattr(studio, "generate_nvidia_image", fake_nvidia)
        monkeypatch.setattr("services.ai.gateway.AIGateway.chat", fake_gateway_chat)

        res = run(studio.generate_or_edit_image(prompt_100))

        assert res["success"] is True
        assert res["provider"] == "nvidia"
        assert res["model"] == "black-forest-labs/flux-3-image-klein"
        assert res["fallback"] is True
        assert len(nvidia_received["prompt"].split()) <= 350
        assert "Tokyo alley" in nvidia_received["prompt"]

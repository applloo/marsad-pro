import base64
import pytest
import image_generation

PNG = b"\x89PNG\r\n\x1a\n" + b"fake-png-payload"


class FakeResponse:
    status_code = 200
    headers = {"x-request-id": "req_test"}
    def json(self):
        return {"data": [{"b64_json": base64.b64encode(PNG).decode()}]}


def test_generate_image_returns_png_and_metadata(monkeypatch):
    calls = {}
    def fake_post(url, **kwargs):
        calls["url"] = url
        calls["kwargs"] = kwargs
        return FakeResponse()
    monkeypatch.setattr(image_generation.requests, "post", fake_post)
    result = image_generation.generate_image("A cinematic scene", "secret", size="1024x1536")
    assert result["image_bytes"] == PNG
    assert result["model"] == "gpt-image-2.6-flare"
    assert result["request_id"] == "req_test"
    assert calls["kwargs"]["json"]["size"] == "1024x1536"
    assert "secret" not in str(result)


def test_generate_image_validates_before_request(monkeypatch):
    monkeypatch.setattr(image_generation.requests, "post", lambda *a, **k: pytest.fail("unexpected request"))
    with pytest.raises(ValueError):
        image_generation.generate_image("", "secret")
    with pytest.raises(ValueError):
        image_generation.generate_image("hello", "secret", model="unknown")
    with pytest.raises(ValueError):
        image_generation.generate_image("hello", "")


def test_generate_image_handles_moderation(monkeypatch):
    class Blocked(FakeResponse):
        status_code = 400
        def json(self):
            return {"error": {"code": "moderation_blocked", "message": "blocked"}}
    monkeypatch.setattr(image_generation.requests, "post", lambda *a, **k: Blocked())
    with pytest.raises(RuntimeError, match="مراجعة المحتوى"):
        image_generation.generate_image("some prompt", "secret")


def test_legacy_models_reject_flexible_custom_sizes_before_request(monkeypatch):
    monkeypatch.setattr(image_generation.requests, "post", lambda *a, **k: pytest.fail("unexpected request"))
    with pytest.raises(ValueError, match="المقاس المختار"):
        image_generation.generate_image("hello", "secret", model="gpt-image-1.5", size="2048x1152")
    assert "رأسي 9:16" not in image_generation.sizes_for_model("gpt-image-1-mini")
    assert "رأسي 9:16" in image_generation.sizes_for_model("gpt-image-2.6-flare")

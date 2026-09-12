from app.core.config import settings
from app.services.collector import _service_key


def test_service_key_decodes_portal_general_key(monkeypatch):
    monkeypatch.setattr(settings, "DATA_GO_KR_API_KEY", "abc%2Bdef%2Fghi%3D%3D")

    assert _service_key() == "abc+def/ghi=="


def test_service_key_keeps_unencoded_key(monkeypatch):
    monkeypatch.setattr(settings, "DATA_GO_KR_API_KEY", "abc+def/ghi==")

    assert _service_key() == "abc+def/ghi=="

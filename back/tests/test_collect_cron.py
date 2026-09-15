"""외부 cron 전용 수집 트리거(POST /api/v1/collect/cron) 검증.

Render 무료 플랜은 유휴 시 서버가 잠들어 APScheduler 정기 실행이 건너뛰어진다.
그래서 외부 cron이 이 엔드포인트를 때려 수집을 돌린다 (docs/배포-Render.md).
"""
import app.services.collect_cycle as collect_cycle_module
from app.core.config import settings

CRON_PATH = "/api/v1/collect/cron"
TOKEN = "test-cron-token-0123456789"


def _stub_cycle(monkeypatch) -> list[int]:
    """실제 수집 대신 호출 횟수만 세는 가짜로 바꾼다 (외부 API를 때리지 않도록)."""
    calls: list[int] = []

    async def fake_run():
        calls.append(1)
        return {"fetched": {}, "saved": 0, "notified": 0, "emailed": 0}

    # 라우터가 import 시점에 이름을 가져가므로 라우터 모듈 쪽도 같이 교체해야 한다.
    import app.api.v1.collect as collect_router

    monkeypatch.setattr(collect_router, "run_collect_cycle", fake_run)
    return calls


def test_returns_404_when_token_not_configured(client, monkeypatch):
    """토큰을 안 정해두면 엔드포인트 자체가 닫혀 있어야 한다 (존재도 알리지 않음)."""
    monkeypatch.setattr(settings, "CRON_TOKEN", "")
    calls = _stub_cycle(monkeypatch)

    res = client.post(CRON_PATH, headers={"X-Cron-Token": "anything"})

    assert res.status_code == 404
    assert calls == []


def test_rejects_wrong_token(client, monkeypatch):
    monkeypatch.setattr(settings, "CRON_TOKEN", TOKEN)
    calls = _stub_cycle(monkeypatch)

    res = client.post(CRON_PATH, headers={"X-Cron-Token": "wrong-token"})

    assert res.status_code == 401
    assert res.json()["error"]["code"] == "INVALID_CRON_TOKEN"
    assert calls == []


def test_rejects_missing_token_header(client, monkeypatch):
    monkeypatch.setattr(settings, "CRON_TOKEN", TOKEN)
    calls = _stub_cycle(monkeypatch)

    res = client.post(CRON_PATH)

    assert res.status_code == 401
    assert calls == []


def test_valid_token_runs_collect_cycle(client, monkeypatch):
    monkeypatch.setattr(settings, "CRON_TOKEN", TOKEN)
    calls = _stub_cycle(monkeypatch)

    res = client.post(CRON_PATH, headers={"X-Cron-Token": TOKEN})

    assert res.status_code == 202
    assert res.json()["data"]["status"] == "accepted"
    # TestClient는 응답 후 백그라운드 작업까지 끝내고 돌아온다
    assert calls == [1]


def test_skips_when_previous_run_still_going(client, monkeypatch):
    """cron이 겹쳐 들어와도 같은 수집을 두 번 돌리지 않는다."""
    monkeypatch.setattr(settings, "CRON_TOKEN", TOKEN)
    calls = _stub_cycle(monkeypatch)
    monkeypatch.setattr(collect_cycle_module, "_running", True)

    res = client.post(CRON_PATH, headers={"X-Cron-Token": TOKEN})

    assert res.status_code == 202
    assert res.json()["data"]["status"] == "already_running"
    assert calls == []


def test_admin_collect_still_requires_admin_jwt(client, monkeypatch):
    """cron 토큰이 관리자용 엔드포인트까지 열어주면 안 된다."""
    monkeypatch.setattr(settings, "CRON_TOKEN", TOKEN)

    res = client.post("/api/v1/collect", headers={"X-Cron-Token": TOKEN})

    assert res.status_code == 401

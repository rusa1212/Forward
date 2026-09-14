import asyncio
from datetime import date, timedelta

import httpx

from app.core.config import settings
from app.services.collector import (
    RECENT_CLOSED_DAYS,
    _service_key,
    fetch_bid_public_info,
    fetch_kstartup,
)


def test_service_key_decodes_portal_general_key(monkeypatch):
    monkeypatch.setattr(settings, "DATA_GO_KR_API_KEY", "abc%2Bdef%2Fghi%3D%3D")

    assert _service_key() == "abc+def/ghi=="


def test_service_key_keeps_unencoded_key(monkeypatch):
    monkeypatch.setattr(settings, "DATA_GO_KR_API_KEY", "abc+def/ghi==")

    assert _service_key() == "abc+def/ghi=="


def _kstartup_page_xml(items: list[dict[str, str]]) -> str:
    item_xml = "".join(
        "<item>" + "".join(f'<col name="{k}">{v}</col>' for k, v in item.items()) + "</item>"
        for item in items
    )
    return f"<response><body><items>{item_xml}</items></body></response>"


def test_fetch_kstartup_keeps_open_and_recent_closed_stops_on_old_page(monkeypatch):
    """모집중 공고와 RECENT_CLOSED_DAYS 이내 마감 공고는 담고, 그보다 오래된 마감
    공고만 있는 페이지를 만나면 그 페이지에서 멈춰 이후 페이지는 호출하지 않는다."""
    monkeypatch.setattr(settings, "DATA_GO_KR_API_KEY", "key")
    today = date.today()
    recent_closed_end = today - timedelta(days=RECENT_CLOSED_DAYS - 1)
    old_closed_end = today - timedelta(days=RECENT_CLOSED_DAYS + 30)

    page1 = [
        {
            "pbanc_sn": "1",
            "biz_pbanc_nm": "open",
            "rcrt_prgs_yn": "Y",
            "pbanc_rcpt_end_dt": (today + timedelta(days=10)).strftime("%Y%m%d"),
        },
        {
            "pbanc_sn": "2",
            "biz_pbanc_nm": "recent-closed",
            "rcrt_prgs_yn": "N",
            "pbanc_rcpt_end_dt": recent_closed_end.strftime("%Y%m%d"),
        },
    ]
    page2 = [
        {
            "pbanc_sn": "3",
            "biz_pbanc_nm": "old-closed-a",
            "rcrt_prgs_yn": "N",
            "pbanc_rcpt_end_dt": old_closed_end.strftime("%Y%m%d"),
        },
        {
            "pbanc_sn": "4",
            "biz_pbanc_nm": "old-closed-b",
            "rcrt_prgs_yn": "N",
            "pbanc_rcpt_end_dt": old_closed_end.strftime("%Y%m%d"),
        },
    ]
    page3 = [
        {
            "pbanc_sn": "5",
            "biz_pbanc_nm": "should-not-be-fetched",
            "rcrt_prgs_yn": "Y",
            "pbanc_rcpt_end_dt": (today + timedelta(days=10)).strftime("%Y%m%d"),
        },
    ]
    pages = {1: page1, 2: page2, 3: page3}
    requested_pages: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        requested_pages.append(page)
        return httpx.Response(200, text=_kstartup_page_xml(pages[page]))

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch_kstartup(client, per_page=2, max_pages=5)

    result = asyncio.run(run())

    assert {it["external_id"] for it in result} == {"1", "2"}
    assert requested_pages == [1, 2]  # page3(=모집중 포함)까지 가지 않고 page2에서 중단


def test_fetch_bid_public_info_keeps_open_and_recent_closed(monkeypatch):
    monkeypatch.setattr(settings, "DATA_GO_KR_API_KEY", "key")
    today = date.today()
    recent_closed_end = today - timedelta(days=RECENT_CLOSED_DAYS - 1)
    old_closed_end = today - timedelta(days=RECENT_CLOSED_DAYS + 30)

    def _row(notice_no: str, close_date: date | None) -> dict:
        return {
            "bidNtceNo": notice_no,
            "bidNtceOrd": "1",
            "bidNtceNm": f"bid-{notice_no}",
            "ntceInsttNm": "agency",
            "dminsttNm": "dept",
            "ntceKindNm": "공고",
            "bidNtceDt": "2026-01-01 00:00:00",
            "bidBeginDt": "2026-01-01 00:00:00",
            "bidClseDt": close_date.strftime("%Y-%m-%d %H:%M:%S") if close_date else None,
        }

    items = [
        _row("open", today + timedelta(days=10)),
        _row("recent-closed", recent_closed_end),
        _row("old-closed", old_closed_end),
        _row("no-close-date", None),
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"response": {"body": {"totalCount": len(items), "items": items}}}
        )

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch_bid_public_info(client, "202601010000", "202601312359")

    result = asyncio.run(run())

    assert {it["external_id"] for it in result} == {
        "open-1",
        "recent-closed-1",
        "no-close-date-1",
    }

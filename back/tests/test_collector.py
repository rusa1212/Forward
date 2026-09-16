import asyncio
from datetime import date, timedelta

import httpx

from app.core.config import settings
from app.services.collector import (
    BID_WINDOW_DAYS,
    MSIT_PAGE_SIZE,
    RECENT_CLOSED_DAYS,
    BidApiError,
    _bid_response_body,
    _service_key,
    _split_bid_windows,
    collect_all,
    fetch_bid_public_info,
    fetch_kstartup,
    fetch_msit,
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


def test_split_bid_windows_splits_long_range_into_max_window_days_chunks():
    # 90일 요청 -> BID_WINDOW_DAYS(30일) 이하 구간들로 쪼개지고, 각 구간은 원래 요청
    # 범위를 벗어나지 않으며 이어붙이면 빈틈/겹침 없이 전체 구간을 덮어야 한다.
    windows = _split_bid_windows("202606160000", "202609142359")

    assert len(windows) >= 3
    for bgn, end in windows:
        from datetime import datetime

        span_days = (datetime.strptime(end, "%Y%m%d%H%M") - datetime.strptime(bgn, "%Y%m%d%H%M")).days
        assert span_days <= BID_WINDOW_DAYS
    assert windows[0][1] == "202609142359"  # 가장 최근 구간의 끝은 요청한 종료 시각
    assert windows[-1][0] == "202606160000"  # 가장 과거 구간의 시작은 요청한 시작 시각


def test_split_bid_windows_short_range_stays_single_window():
    windows = _split_bid_windows("202601010000", "202601202359")
    assert windows == [("202601010000", "202601202359")]


def test_fetch_bid_public_info_survives_one_window_failing(monkeypatch):
    """구간 하나가 실패(타임아웃 등)해도 나머지 구간의 정상 데이터는 반환돼야 한다."""
    monkeypatch.setattr(settings, "DATA_GO_KR_API_KEY", "key")

    def handler(request: httpx.Request) -> httpx.Response:
        bgn = request.url.params["inqryBgnDt"]
        if bgn == "202606160000":
            raise httpx.ReadTimeout("simulated timeout", request=request)
        return httpx.Response(
            200,
            json={
                "response": {
                    "header": {"resultCode": "00", "resultMsg": "정상"},
                    "body": {
                        "totalCount": 1,
                        "items": [
                            {
                                "bidNtceNo": "ok",
                                "bidNtceOrd": "1",
                                "bidNtceNm": "정상 구간 공고",
                                "ntceInsttNm": "agency",
                                "dminsttNm": "dept",
                                "ntceKindNm": "공고",
                                "bidNtceDt": "2026-09-01 00:00:00",
                                "bidBeginDt": "2026-09-01 00:00:00",
                                "bidClseDt": None,
                            }
                        ],
                    },
                }
            },
        )

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch_bid_public_info(client, "202606160000", "202609142359")

    result = asyncio.run(run())

    assert {it["external_id"] for it in result} == {"ok-1"}


def test_bid_response_body_raises_on_error_payload():
    """resultCode가 00이 아니면(예: 조회기간 초과) 조용히 빈 값으로 넘어가지 않고 예외를 던진다."""
    error_payload = {
        "nkoneps.com.response.ResponseError": {
            "header": {"resultCode": "07", "resultMsg": "입력범위값 초과 에러"}
        }
    }
    try:
        _bid_response_body(error_payload)
        assert False, "BidApiError가 발생해야 한다"
    except BidApiError as e:
        assert "07" in str(e)


def test_bid_response_body_returns_body_on_success():
    payload = {"response": {"header": {"resultCode": "00", "resultMsg": "정상"}, "body": {"totalCount": 0}}}
    assert _bid_response_body(payload) == {"totalCount": 0}


def test_fetch_bid_public_info_survives_api_error_response():
    """구간 하나가 API 오류(resultCode != 00)로 실패해도 예외를 전파하지 않고 빈 결과로 넘어간다."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "nkoneps.com.response.ResponseError": {
                    "header": {"resultCode": "07", "resultMsg": "입력범위값 초과 에러"}
                }
            },
        )

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch_bid_public_info(client, "202601010000", "202601312359")

    result = asyncio.run(run())
    assert result == []


def test_collect_all_isolates_source_failures(monkeypatch):
    """한 소스가 실패해도 나머지 소스는 정상적으로 저장 대상에 포함돼야 한다."""
    monkeypatch.setattr(settings, "DATA_GO_KR_API_KEY", "key")

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "BidPublicInfoService" in url:
            raise httpx.ReadTimeout("simulated timeout", request=request)
        if "kisedKstartupService01" in url:
            return httpx.Response(200, text="<response><body><items></items></body></response>")
        # msit
        return httpx.Response(200, json={"response": [{"body": {"items": []}}]})

    async def run():
        import app.services.collector as collector_module

        orig_client_cls = httpx.AsyncClient

        class PatchedClient(orig_client_cls):
            def __init__(self, *args, **kwargs):
                kwargs["transport"] = httpx.MockTransport(handler)
                super().__init__(*args, **kwargs)

        monkeypatch.setattr(collector_module.httpx, "AsyncClient", PatchedClient)
        return await collect_all("202601010000", "202601312359")

    result = asyncio.run(run())

    assert result["narajangteo"] == []  # 실패한 소스는 빈 목록
    assert result["kstartup"] == []  # 정상 응답(빈 목록)은 그대로
    assert result["msit"] == []


def _msit_page_json(items: list[dict[str, str]]) -> dict:
    return {
        "response": [
            {"header": {"resultCode": "00", "resultMsg": "NORMAL_CODE"}},
            {
                "body": {
                    "pageNo": "1",
                    "totalCount": 4253,
                    "numOfRows": MSIT_PAGE_SIZE,
                    "items": [
                        {
                            "item": {
                                "subject": item["subject"],
                                "pressDt": item["pressDt"],
                                "deptName": "과기정통부",
                                "viewUrl": f"https://www.msit.go.kr/bbs/view.do?nttSeqNo={item['id']}",
                            }
                        }
                        for item in items
                    ],
                }
            },
        ]
    }


def test_fetch_msit_pages_through_fixed_page_size_and_stops_on_old_page(monkeypatch):
    """이 API는 numOfRows 요청값을 무시하고 언제나 MSIT_PAGE_SIZE(10)건씩만 돌려준다.
    그래서 "받은 건수 < 요청 건수 = 마지막 페이지" 종료 조건이 1페이지에서 참이 되지 않도록
    기본 요청 건수가 실제 페이지 크기와 같아야 한다 — 어긋나면 10건만 걷히고 끝난다.
    그리고 보도일이 RECENT_CLOSED_DAYS보다 오래된 페이지를 만나면 거기서 멈춘다."""
    monkeypatch.setattr(settings, "DATA_GO_KR_API_KEY", "key")
    today = date.today()
    recent = (today - timedelta(days=RECENT_CLOSED_DAYS - 1)).strftime("%Y-%m-%d")
    old = (today - timedelta(days=RECENT_CLOSED_DAYS + 30)).strftime("%Y-%m-%d")

    def page(prefix: str, press_dt: str) -> list[dict[str, str]]:
        return [
            {"id": f"{prefix}{i}", "subject": f"{prefix}-{i}", "pressDt": press_dt}
            for i in range(MSIT_PAGE_SIZE)
        ]

    pages = {1: page("a", recent), 2: page("b", recent), 3: page("c", old), 4: page("d", recent)}
    requested_pages: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page_no = int(request.url.params["pageNo"])
        requested_pages.append(page_no)
        # 실제 API와 똑같이, 요청한 numOfRows와 무관하게 MSIT_PAGE_SIZE건만 돌려준다.
        return httpx.Response(200, json=_msit_page_json(pages[page_no]))

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch_msit(client)

    result = asyncio.run(run())

    assert len(result) == 2 * MSIT_PAGE_SIZE  # 1페이지에서 멈추지 않았다
    assert {it["external_id"] for it in result} == {f"a{i}" for i in range(MSIT_PAGE_SIZE)} | {
        f"b{i}" for i in range(MSIT_PAGE_SIZE)
    }
    assert requested_pages == [1, 2, 3]  # 오래된 page3에서 중단, page4는 호출하지 않는다


def test_fetch_msit_has_no_reception_dates(monkeypatch):
    """이 API 응답에는 접수 시작/마감 필드가 없다. 그래서 수집 결과도 날짜가 비어 있고
    (파서 누락이 아님), 저장되면 "기한미정"으로 분류된다."""
    monkeypatch.setattr(settings, "DATA_GO_KR_API_KEY", "key")
    today = date.today().strftime("%Y-%m-%d")

    def handler(request: httpx.Request) -> httpx.Response:
        if int(request.url.params["pageNo"]) > 1:
            return httpx.Response(200, json=_msit_page_json([]))
        return httpx.Response(
            200, json=_msit_page_json([{"id": "1", "subject": "공고", "pressDt": today}])
        )

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch_msit(client)

    result = asyncio.run(run())

    assert len(result) == 1
    assert result[0]["start_date"] is None
    assert result[0]["end_date"] is None
    assert result[0]["announce_date"] == date.today()

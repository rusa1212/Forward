"""공공데이터포털 API 3종 호출 + 공고 필드 정규화

- 창업진흥원 K-Startup: 사업공고 (XML, col name= 구조)
- 조달청 나라장터: 입찰공고정보 (JSON)
- 과학기술정보통신부: 사업공고 (JSON)

세 API 모두 같은 DATA_GO_KR_API_KEY(포털의 일반 인증키)를 공용으로 사용합니다.
URL 인코딩된 형태로 발급돼도 요청 전에 디코딩해 httpx가 정확히 한 번만 인코딩합니다.
"""
import asyncio
import logging
from datetime import date, datetime, timedelta
from urllib.parse import parse_qs, unquote, urlparse
from xml.etree import ElementTree

import httpx

from app.core.config import settings

logger = logging.getLogger("app.collector")

TIMEOUT = 15.0

# 나라장터는 실측 결과(2026-09) numOfRows=100 페이지 하나가 TIMEOUT(15초)을 넘겨
# httpx.ReadTimeout이 나는 경우가 있었다 — 응답 페이로드가 다른 두 소스보다 훨씬 크다.
# 그래서 이 API 호출에는 더 넉넉한 타임아웃을 따로 둔다.
BID_TIMEOUT = 25.0

# 소스별 한 번 수집할 때 API를 최대 몇 페이지까지 호출할지 안전장치.
# 100건/페이지 기준 MAX_PAGES=30이면 소스당 최대 3,000건 — 공공데이터포털 일반 인증키
# 일일 호출 한도(보통 1,000회)를 감안한 값이니, 실제로 이 한도에 자주 걸리면 늘릴 것.
MAX_PAGES = 30

# 나라장터는 실측 결과 최근 30일치만도 totalCount가 11,000건을 넘고(2026-09 기준),
# 열림/닫힘이 페이지 전체에 고르게 섞여있어(공고일 오름차순 정렬) kstartup처럼
# "마감된 항목만 나오는 페이지에서 중단"하는 요령을 쓸 수 없다. 그래서 API가 알려주는
# totalCount만큼 끝까지 넘기되, totalCount가 비정상적으로 크게 와도 무한 호출하지 않도록
# 훨씬 큰 별도 안전장치를 둔다(100건/페이지 기준 최대 30,000건).
BID_MAX_PAGES = 300

# R&D Monitor 회의 피드백(docs/feedback.md 1번): 진행 중인 공고뿐 아니라 최근 마감된
# 공고도 일정 기간 함께 보여달라는 요청 — 마감 후에도 이 기간만큼은 목록에 남겨둔다.
RECENT_CLOSED_DAYS = 90

# 나라장터는 조회 기간(inqryBgnDt~inqryEndDt)이 필수라 "전체 기간"을 조회할 수 없다.
# "오늘 하루"만 보면 이미 공고돼서 아직 마감 안 된 과거 공고를 놓치므로, 모집 중인 공고를
# 폭넓게 잡으면서 동시에 RECENT_CLOSED_DAYS 이내에 마감된 공고까지 함께 잡을 수 있도록
# 최근 N일을 기본 조회 기간으로 삼는다(RECENT_CLOSED_DAYS와 동일하게 맞춤).
BID_LOOKBACK_DAYS = RECENT_CLOSED_DAYS


def _service_key() -> str:
    """포털의 단일 일반 인증키를 httpx가 정확히 한 번만 URL 인코딩하게 한다."""
    return unquote(settings.DATA_GO_KR_API_KEY)


def _parse_date(value: str | None, fmt: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, fmt).date()
    except ValueError:
        return None


def today_bid_date_range() -> tuple[str, str]:
    """나라장터 조회 파라미터(YYYYMMDDHHMM) 기본값: 최근 BID_LOOKBACK_DAYS일 00:00 ~ 오늘 23:59.

    함수 이름은 "오늘"이지만 실제로는 모집 중인 공고를 폭넓게 잡기 위한 기본 조회 기간을
    돌려준다 (collect.py/scheduler.py 호출부와의 하위 호환을 위해 이름은 유지).
    """
    today = datetime.now()
    start = today - timedelta(days=BID_LOOKBACK_DAYS)
    return f"{start.strftime('%Y%m%d')}0000", f"{today.strftime('%Y%m%d')}2359"


async def fetch_kstartup(
    client: httpx.AsyncClient, per_page: int = 100, max_pages: int = MAX_PAGES
) -> list[dict]:
    """창업진흥원 K-Startup 사업공고. 응답이 <col name="...">value</col> 형태의 XML.

    실측 결과 이 API는 마감일 기준 최신순으로 내려오고 totalCount가 30,000건을 넘는
    역대 전체 아카이브다(2026-09 기준). 그 전부를 매번 훑는 건 비현실적이라, 한 페이지
    전체가 모집중(Y)도 아니고 RECENT_CLOSED_DAYS 이내에 마감된 것도 아니면 그 뒤로는
    더 오래된 마감 공고만 나온다고 보고 그 페이지에서 멈춘다. "모집 중인 공고 + 최근
    RECENT_CLOSED_DAYS일 이내 마감 공고"가 목적이므로 반환값에는 그 조건을 만족하는
    항목만 담는다 — 그보다 오래된 마감 항목은 중단 시점 판단에만 쓰고 버린다.
    """
    cutoff_date = date.today() - timedelta(days=RECENT_CLOSED_DAYS)
    items = []
    for page in range(1, max_pages + 1):
        res = await client.get(
            "https://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01",
            params={"serviceKey": _service_key(), "page": page, "perPage": per_page},
            timeout=TIMEOUT,
        )
        res.raise_for_status()
        root = ElementTree.fromstring(res.text)

        page_items = []
        for item_el in root.findall(".//item"):
            row = {col.get("name"): (col.text or "") for col in item_el.findall("col")}
            page_items.append(
                {
                    "source": "kstartup",
                    "external_id": row.get("pbanc_sn"),
                    "title": row.get("biz_pbanc_nm"),
                    "agency": row.get("pbanc_ntrp_nm"),
                    "department": row.get("biz_prch_dprt_nm"),
                    "status": row.get("rcrt_prgs_yn"),  # Y: 모집중, N: 마감
                    "announce_date": None,
                    "start_date": _parse_date(row.get("pbanc_rcpt_bgng_dt"), "%Y%m%d"),
                    "end_date": _parse_date(row.get("pbanc_rcpt_end_dt"), "%Y%m%d"),
                    "original_url": row.get("detl_pg_url"),
                    "content": row.get("pbanc_ctnt"),
                }
            )

        if not page_items:
            break
        keep_items = [
            it
            for it in page_items
            if it["status"] == "Y" or (it["end_date"] is not None and it["end_date"] >= cutoff_date)
        ]
        items.extend(keep_items)
        if not keep_items:
            break
        if len(page_items) < per_page:
            break

    return items


class BidApiError(RuntimeError):
    """나라장터 API가 정상(resultCode 00)이 아닌 응답을 돌려줬을 때."""


def _bid_response_body(payload: dict) -> dict:
    """정상 응답의 body를 꺼낸다. 실패 응답은 조용히 넘어가지 않고 예외로 드러낸다.

    이 API는 파라미터 오류(예: 조회기간이 상한을 넘음) 시 HTTP 200이지만 "response" 키
    없이 {"nkoneps.com.response.ResponseError": {"header": {...}}} 형태로 온다.
    과거엔 이걸 .get("response", {})로 조용히 빈 값 취급해 나라장터 데이터가 소리 없이
    누락됐다(R&D Monitor 회의 피드백 2번) — 그래서 명시적으로 감지해 예외를 던진다.
    """
    response = payload.get("response")
    if response is None:
        error = next(iter(payload.values()), {}) if payload else {}
        header = error.get("header", {}) if isinstance(error, dict) else {}
        raise BidApiError(
            f"나라장터 API 오류 응답: resultCode={header.get('resultCode')} "
            f"resultMsg={header.get('resultMsg')}"
        )
    header = response.get("header", {})
    result_code = header.get("resultCode")
    if result_code not in (None, "00"):
        raise BidApiError(
            f"나라장터 API 오류 응답: resultCode={result_code} resultMsg={header.get('resultMsg')}"
        )
    return response.get("body", {})


# 실측 결과 나라장터 API는 조회기간(inqryBgnDt~inqryEndDt)이 31일을 넘으면 무조건
# resultCode 07(입력범위값 초과 에러)로 실패한다(2026-09 기준). RECENT_CLOSED_DAYS까지
# 폭넓게 조회하려면 이 상한 이하 구간으로 쪼개 여러 번 호출해야 한다.
BID_WINDOW_DAYS = 30


def _split_bid_windows(
    inqry_bgn_dt: str, inqry_end_dt: str, window_days: int = BID_WINDOW_DAYS
) -> list[tuple[str, str]]:
    """(inqry_bgn_dt, inqry_end_dt) 구간을 API 상한 이하의 연속된 구간들로 쪼갠다."""
    start = datetime.strptime(inqry_bgn_dt, "%Y%m%d%H%M")
    end = datetime.strptime(inqry_end_dt, "%Y%m%d%H%M")
    windows = []
    window_end = end
    while window_end > start:
        window_start = max(start, window_end - timedelta(days=window_days))
        windows.append((window_start.strftime("%Y%m%d%H%M"), window_end.strftime("%Y%m%d%H%M")))
        window_end = window_start
    return windows or [(inqry_bgn_dt, inqry_end_dt)]


async def _fetch_bid_window(
    client: httpx.AsyncClient,
    inqry_bgn_dt: str,
    inqry_end_dt: str,
    num_of_rows: int,
    max_pages: int,
    cutoff_date: date,
) -> list[dict]:
    """단일 조회 구간(<= BID_WINDOW_DAYS일) 내 입찰공고 전체를 페이지네이션으로 가져온다.

    열림/닫힘 공고가 페이지 전체에 고르게 섞여 나와(공고일 오름차순 정렬) "마감 공고만
    나오는 페이지에서 중단" 같은 지름길을 쓸 수 없다. 그래서 응답의 totalCount를 그대로
    신뢰해 구간 내 전체를 끝까지 가져온다 — max_pages는 totalCount가 비정상적으로 크게
    와도 무한 호출하지 않기 위한 안전장치일 뿐, 정상 응답에서는 도달하지 않는 게 정상이다.
    """
    items = []
    fetched_count = 0
    total_count: int | None = None
    for page_no in range(1, max_pages + 1):
        res = await client.get(
            "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServc",
            params={
                "serviceKey": _service_key(),
                "numOfRows": num_of_rows,
                "pageNo": page_no,
                "type": "json",
                "inqryDiv": 1,
                "inqryBgnDt": inqry_bgn_dt,
                "inqryEndDt": inqry_end_dt,
            },
            timeout=BID_TIMEOUT,
        )
        res.raise_for_status()
        body = _bid_response_body(res.json())
        total_count = body.get("totalCount", total_count)
        raw_items = body.get("items") or []

        page_items = []
        for row in raw_items:
            notice_no = row.get("bidNtceNo")
            notice_ord = row.get("bidNtceOrd")
            page_items.append(
                {
                    "source": "narajangteo",
                    "external_id": f"{notice_no}-{notice_ord}" if notice_ord else notice_no,
                    "title": row.get("bidNtceNm"),
                    "agency": row.get("ntceInsttNm"),
                    "department": row.get("dminsttNm"),
                    "status": row.get("ntceKindNm"),
                    "announce_date": _parse_date(row.get("bidNtceDt"), "%Y-%m-%d %H:%M:%S"),
                    "start_date": _parse_date(row.get("bidBeginDt"), "%Y-%m-%d %H:%M:%S"),
                    "end_date": _parse_date(row.get("bidClseDt"), "%Y-%m-%d %H:%M:%S"),
                    "original_url": row.get("bidNtceDtlUrl") or row.get("bidNtceUrl"),
                    "content": None,
                }
            )

        if not page_items:
            break
        fetched_count += len(page_items)
        items.extend(
            it for it in page_items if it["end_date"] is None or it["end_date"] >= cutoff_date
        )
        if len(page_items) < num_of_rows:
            break
        if total_count is not None and fetched_count >= total_count:
            break

    return items


async def fetch_bid_public_info(
    client: httpx.AsyncClient,
    inqry_bgn_dt: str,
    inqry_end_dt: str,
    num_of_rows: int = 100,
    max_pages: int = BID_MAX_PAGES,
) -> list[dict]:
    """조달청 나라장터 입찰공고정보. inqry_bgn_dt/inqry_end_dt 형식: YYYYMMDDHHMM.

    요청 구간이 BID_WINDOW_DAYS(API 상한 이하)보다 길면 여러 구간으로 나눠 병렬 호출한 뒤
    합친다(_split_bid_windows). "모집 중인 공고 + 최근 RECENT_CLOSED_DAYS일 이내 마감
    공고"가 목적이므로, 구간별로도 아직 마감되지 않았거나(bidClseDt가 없거나 오늘 이후)
    마감된 지 RECENT_CLOSED_DAYS일이 안 된 항목만 담는다 — 그보다 오래전에 마감된 입찰은
    버린다. 구간 경계에 걸쳐 같은 공고가 중복 조회될 수 있어 external_id 기준으로 합친다.

    구간 하나가 실패(타임아웃 등)해도 나머지 구간은 그대로 살려서 반환한다 — 예전엔 구간
    하나만 실패해도 전체가 예외로 죽어(나머지 구간의 정상 데이터까지 날아가고, collect_all의
    다른 소스까지 같이 취소됨) "나라장터가 통째로 안 걷힌다"는 문제가 생겼다
    (R&D Monitor 회의 피드백 2번).
    """
    cutoff_date = date.today() - timedelta(days=RECENT_CLOSED_DAYS)
    windows = _split_bid_windows(inqry_bgn_dt, inqry_end_dt)
    window_results = await asyncio.gather(
        *(
            _fetch_bid_window(client, w_bgn, w_end, num_of_rows, max_pages, cutoff_date)
            for w_bgn, w_end in windows
        ),
        return_exceptions=True,
    )

    merged: dict[str, dict] = {}
    for (w_bgn, w_end), result in zip(windows, window_results):
        if isinstance(result, BaseException):
            logger.warning("나라장터 구간 수집 실패 (%s~%s): %s", w_bgn, w_end, result)
            continue
        for item in result:
            if item["external_id"]:
                merged[item["external_id"]] = item
    return list(merged.values())


# 과기정통부 API는 numOfRows 요청값을 무시하고 언제나 10건씩만 돌려준다
# (2026-09 실측: 10/20/50/100/1000 무엇을 보내도 응답의 numOfRows=10).
# 이 값을 실제와 맞춰두지 않으면 아래 "받은 건수 < 요청 건수 = 마지막 페이지" 종료 조건이
# 1페이지에서 바로 참이 되어, totalCount 4,253건 중 10건만 걷힌다.
MSIT_PAGE_SIZE = 10


async def fetch_msit(
    client: httpx.AsyncClient, num_of_rows: int = MSIT_PAGE_SIZE, max_pages: int = MAX_PAGES
) -> list[dict]:
    """과학기술정보통신부 사업공고.

    보도일(pressDt) 최신순으로 내려오고 2013년까지 거슬러 올라가는 전체 아카이브라
    (2026-09 기준 totalCount 4,253건), K-Startup과 같은 기준으로 최근 RECENT_CLOSED_DAYS일
    이내에 보도된 공고까지만 담고 그보다 오래된 페이지에 닿으면 멈춘다.
    10건/페이지 기준 최근 90일은 약 10페이지라 max_pages(30)에는 닿지 않는 게 정상이다.

    ⚠️ 이 API 응답에는 접수 시작/마감 필드가 아예 없다 — deptName, subject, pressDt,
    viewUrl, managerName, managerTel, files가 전부다. 그래서 여기서 담는 공고는
    reception_start/end가 비어 "기한미정"으로 분류된다(파서 누락이 아니라 원본에 없는 것).
    """
    cutoff_date = date.today() - timedelta(days=RECENT_CLOSED_DAYS)
    items = []
    for page_no in range(1, max_pages + 1):
        res = await client.get(
            "https://apis.data.go.kr/1721000/msitannouncementinfo/businessAnnouncMentList",
            params={
                "ServiceKey": _service_key(),
                "pageNo": page_no,
                "numOfRows": num_of_rows,
                "returnType": "json",
            },
            timeout=TIMEOUT,
        )
        res.raise_for_status()
        body_wrapper = next((b for b in res.json().get("response", []) if "body" in b), {})
        raw_items = body_wrapper.get("body", {}).get("items") or []

        page_items = []
        for wrapper in raw_items:
            row = wrapper.get("item", {})
            view_url = row.get("viewUrl") or ""
            query = parse_qs(urlparse(view_url).query)
            external_id = (query.get("nttSeqNo") or [None])[0] or view_url

            page_items.append(
                {
                    "source": "msit",
                    "external_id": external_id,
                    "title": row.get("subject"),
                    "agency": "과학기술정보통신부",
                    "department": row.get("deptName"),
                    "status": None,
                    "announce_date": _parse_date(row.get("pressDt"), "%Y-%m-%d"),
                    "start_date": None,
                    "end_date": None,
                    "original_url": view_url or None,
                    "content": None,
                }
            )

        if not page_items:
            break
        # pressDt가 없는 항목은 오래된 건지 판단할 수 없으므로 버리지 않고 함께 담는다.
        keep_items = [
            it
            for it in page_items
            if it["announce_date"] is None or it["announce_date"] >= cutoff_date
        ]
        items.extend(keep_items)
        if not keep_items:
            break
        if len(page_items) < num_of_rows:
            break

    return items


async def collect_all(inqry_bgn_dt: str, inqry_end_dt: str) -> dict[str, list[dict]]:
    """3개 소스를 병렬로 호출해 소스별 정규화된 공고 목록을 반환.

    한 소스가 실패해도 나머지 소스는 정상 저장돼야 하므로(예: 나라장터가 API 오류로
    죽어도 K-Startup/과기정통부는 이번 수집분을 그대로 반영), 소스별 실패를 서로
    전파시키지 않고 실패한 소스만 빈 목록으로 돌려준다.
    """
    sources = ("kstartup", "narajangteo", "msit")
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            fetch_kstartup(client),
            fetch_bid_public_info(client, inqry_bgn_dt, inqry_end_dt),
            fetch_msit(client),
            return_exceptions=True,
        )

    items_by_source: dict[str, list[dict]] = {}
    for source, result in zip(sources, results):
        if isinstance(result, BaseException):
            logger.warning("%s 수집 실패: %s", source, result)
            items_by_source[source] = []
        else:
            items_by_source[source] = result
    return items_by_source

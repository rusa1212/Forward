"""공공데이터포털 API 3종 호출 + 공고 필드 정규화

- 창업진흥원 K-Startup: 사업공고 (XML, col name= 구조)
- 조달청 나라장터: 입찰공고정보 (JSON)
- 과학기술정보통신부: 사업공고 (JSON)

세 API 모두 같은 DATA_GO_KR_API_KEY(포털의 일반 인증키)를 공용으로 사용합니다.
URL 인코딩된 형태로 발급돼도 요청 전에 디코딩해 httpx가 정확히 한 번만 인코딩합니다.
"""
import asyncio
from datetime import date, datetime, timedelta
from urllib.parse import parse_qs, unquote, urlparse
from xml.etree import ElementTree

import httpx

from app.core.config import settings

TIMEOUT = 15.0

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

# 나라장터는 조회 기간(inqryBgnDt~inqryEndDt)이 필수라 "전체 기간"을 조회할 수 없다.
# "오늘 하루"만 보면 이미 공고돼서 아직 마감 안 된 과거 공고를 놓치므로,
# 모집 중인 공고를 폭넓게 잡기 위해 최근 N일을 기본 조회 기간으로 삼는다.
BID_LOOKBACK_DAYS = 30


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
    전체가 이미 마감(rcrt_prgs_yn=="N")된 항목뿐이면 그 뒤로는 더 오래된 마감 공고만
    나온다고 보고 그 페이지에서 멈춘다. "모집 중인 모든 공고"가 목적이므로 반환값에는
    모집중(Y) 항목만 담는다 — 마감(N) 항목은 중단 시점 판단에만 쓰고 버린다.
    """
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
        open_items = [it for it in page_items if it["status"] == "Y"]
        items.extend(open_items)
        if not open_items:
            break
        if len(page_items) < per_page:
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

    kstartup과 달리 열림/닫힘 공고가 페이지 전체에 고르게 섞여 나와(공고일 오름차순
    정렬) "마감 공고만 나오는 페이지에서 중단" 같은 지름길을 쓸 수 없다. 그래서 응답의
    totalCount를 그대로 신뢰해 조회 기간(inqry_bgn_dt~inqry_end_dt) 내 전체를 끝까지
    가져온다 — BID_MAX_PAGES는 totalCount가 비정상적으로 크게 와도 무한 호출하지
    않기 위한 안전장치일 뿐, 정상 응답에서는 도달하지 않는 게 정상이다.

    "모집 중인 모든 공고"가 목적이므로 반환값에는 아직 마감되지 않은(bidClseDt가
    없거나 오늘 이후인) 항목만 담는다 — 이미 마감된 입찰은 페이지 순회 진행 판단에만
    쓰고 버린다.
    """
    items = []
    fetched_count = 0
    today = date.today()
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
            timeout=TIMEOUT,
        )
        res.raise_for_status()
        body = res.json().get("response", {}).get("body", {})
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
        items.extend(it for it in page_items if it["end_date"] is None or it["end_date"] >= today)
        if len(page_items) < num_of_rows:
            break
        if total_count is not None and fetched_count >= total_count:
            break

    return items


async def fetch_msit(
    client: httpx.AsyncClient, num_of_rows: int = 100, max_pages: int = MAX_PAGES
) -> list[dict]:
    """과학기술정보통신부 사업공고.

    응답이 num_of_rows보다 적어질 때까지(=마지막 페이지) 페이지를 계속 넘겨 전체를 모은다.
    """
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
        items.extend(page_items)
        if len(page_items) < num_of_rows:
            break

    return items


async def collect_all(inqry_bgn_dt: str, inqry_end_dt: str) -> dict[str, list[dict]]:
    """3개 소스를 병렬로 호출해 소스별 정규화된 공고 목록을 반환."""
    async with httpx.AsyncClient() as client:
        kstartup_items, bid_items, msit_items = await asyncio.gather(
            fetch_kstartup(client),
            fetch_bid_public_info(client, inqry_bgn_dt, inqry_end_dt),
            fetch_msit(client),
        )

    return {"kstartup": kstartup_items, "narajangteo": bid_items, "msit": msit_items}

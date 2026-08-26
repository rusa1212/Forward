"""공공데이터포털 API 3종 호출 + 공고 필드 정규화

- 창업진흥원 K-Startup: 사업공고 (XML, col name= 구조)
- 조달청 나라장터: 입찰공고정보 (JSON)
- 과학기술정보통신부: 사업공고 (JSON)

세 API 모두 같은 DATA_GO_KR_API_KEY(디코딩 키)를 공용으로 사용합니다.
"""
import asyncio
from datetime import date, datetime
from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree

import httpx

from app.core.config import settings

TIMEOUT = 15.0


def _parse_date(value: str | None, fmt: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, fmt).date()
    except ValueError:
        return None


async def fetch_kstartup(client: httpx.AsyncClient, page: int = 1, per_page: int = 100) -> list[dict]:
    """창업진흥원 K-Startup 사업공고. 응답이 <col name="...">value</col> 형태의 XML."""
    res = await client.get(
        "https://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01",
        params={"serviceKey": settings.DATA_GO_KR_API_KEY, "page": page, "perPage": per_page},
        timeout=TIMEOUT,
    )
    res.raise_for_status()
    root = ElementTree.fromstring(res.text)

    items = []
    for item_el in root.findall(".//item"):
        row = {col.get("name"): (col.text or "") for col in item_el.findall("col")}
        items.append(
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
    return items


async def fetch_bid_public_info(
    client: httpx.AsyncClient,
    inqry_bgn_dt: str,
    inqry_end_dt: str,
    num_of_rows: int = 100,
    page_no: int = 1,
) -> list[dict]:
    """조달청 나라장터 입찰공고정보. inqry_bgn_dt/inqry_end_dt 형식: YYYYMMDDHHMM."""
    res = await client.get(
        "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServc",
        params={
            "serviceKey": settings.DATA_GO_KR_API_KEY,
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
    raw_items = body.get("items") or []

    items = []
    for row in raw_items:
        notice_no = row.get("bidNtceNo")
        notice_ord = row.get("bidNtceOrd")
        items.append(
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
    return items


async def fetch_msit(client: httpx.AsyncClient, page_no: int = 1, num_of_rows: int = 100) -> list[dict]:
    """과학기술정보통신부 사업공고."""
    res = await client.get(
        "https://apis.data.go.kr/1721000/msitannouncementinfo/businessAnnouncMentList",
        params={
            "ServiceKey": settings.DATA_GO_KR_API_KEY,
            "pageNo": page_no,
            "numOfRows": num_of_rows,
            "returnType": "json",
        },
        timeout=TIMEOUT,
    )
    res.raise_for_status()
    body_wrapper = next((b for b in res.json().get("response", []) if "body" in b), {})
    raw_items = body_wrapper.get("body", {}).get("items") or []

    items = []
    for wrapper in raw_items:
        row = wrapper.get("item", {})
        view_url = row.get("viewUrl") or ""
        query = parse_qs(urlparse(view_url).query)
        external_id = (query.get("nttSeqNo") or [None])[0] or view_url

        items.append(
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

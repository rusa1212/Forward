"""키워드 CRUD (5주차 1차 작업 순서 10)

인증된 사용자만 자신의 키워드를 조회·등록·삭제할 수 있습니다.
(대시보드/이메일 알림 ON-OFF 같은 알림 설정은 이번 범위에 없고, alert_settings 테이블이
따로 필요한 다음 작업입니다 — db-design.md 참고)
"""
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.errors import AppError
from app.db.models import Keyword, User
from app.db.session import get_db

router = APIRouter(prefix="/keywords", tags=["keywords"])


def _serialize(row: Keyword) -> dict:
    return {"id": str(row.id), "keyword": row.keyword, "createdAt": row.created_at}


@router.get("")
def list_keywords(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Keyword).where(Keyword.user_id == current_user.id).order_by(Keyword.created_at.asc())
    rows = db.execute(stmt).scalars().all()
    return {"success": True, "data": [_serialize(row) for row in rows]}


class KeywordCreateRequest(BaseModel):
    keyword: str = Field(min_length=1, max_length=50)


@router.post("")
def create_keyword(
    body: KeywordCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    keyword = body.keyword.strip()
    if not keyword:
        raise AppError(400, "EMPTY_KEYWORD", "키워드를 입력해주세요.")

    exists = db.execute(
        select(Keyword).where(Keyword.user_id == current_user.id, Keyword.keyword == keyword)
    ).scalar_one_or_none()
    if exists is not None:
        raise AppError(409, "DUPLICATE_KEYWORD", "이미 등록된 키워드입니다.")

    row = Keyword(user_id=current_user.id, keyword=keyword)
    db.add(row)
    db.commit()
    db.refresh(row)

    return {"success": True, "data": _serialize(row)}


@router.delete("/{keyword_id}")
def delete_keyword(
    keyword_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        parsed_id = str(uuid.UUID(keyword_id))  # CHAR(36) PK — 형식 검증 후 문자열로 비교
    except ValueError:
        raise AppError(404, "KEYWORD_NOT_FOUND", "존재하지 않는 키워드입니다.")

    row = db.execute(
        select(Keyword).where(Keyword.id == parsed_id, Keyword.user_id == current_user.id)
    ).scalar_one_or_none()
    if row is None:
        # 다른 사용자의 키워드이거나 존재하지 않는 경우 — 둘 다 같은 404로 응답 (소유권 노출 방지)
        raise AppError(404, "KEYWORD_NOT_FOUND", "존재하지 않는 키워드입니다.")

    db.delete(row)
    db.commit()

    return {"success": True, "data": {"message": "키워드가 삭제되었습니다."}}

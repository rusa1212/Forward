"""마이페이지 - 내 정보 조회/수정 + 비밀번호 변경 (5주차 우선순위 P1)

FE MyPage/ProfileTab.tsx가 지금은 이름/이메일 등을 고정값으로 보여주고
"정보 수정"/"비밀번호 변경" 버튼이 아무 동작도 안 하는데, 이 두 버튼이 호출할
API입니다. 이름/연락처/아이디는 우리 스키마에 없는 필드라(현재 users/employees
테이블에 존재하지 않음) 이번 범위에서는 이메일 변경 + 비밀번호 변경만 다룹니다.
FE 쪽 이름/연락처/아이디 표시는 그대로 두거나, 필요하면 스키마 변경을 별도로 논의해야 합니다.
"""
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.auth import _hash_password, _verify_password, get_current_user
from app.core.errors import AppError
from app.db.models import AlertSetting, Employee, User
from app.db.session import get_db

router = APIRouter(tags=["me"])


def _serialize_me(user: User, employee: Employee | None) -> dict:
    return {
        "id": str(user.id),
        "empId": user.emp_id,
        "name": employee.name if employee else None,
        "department": employee.department if employee else None,
        "email": user.email,
    }


@router.get("/me")
def get_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    employee = db.get(Employee, current_user.emp_id)
    return {"success": True, "data": _serialize_me(current_user, employee)}


class UpdateMeRequest(BaseModel):
    email: EmailStr


@router.patch("/me")
def update_me(
    body: UpdateMeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.email != current_user.email:
        exists = db.execute(
            select(User).where(User.email == body.email, User.id != current_user.id)
        ).scalar_one_or_none()
        if exists is not None:
            raise AppError(409, "DUPLICATE_EMAIL", "이미 사용 중인 이메일입니다.")
        current_user.email = body.email
        db.commit()
        db.refresh(current_user)

    employee = db.get(Employee, current_user.emp_id)
    return {"success": True, "data": _serialize_me(current_user, employee)}


class ChangePasswordRequest(BaseModel):
    currentPw: str = Field(min_length=1, max_length=72)
    newPw: str = Field(min_length=6, max_length=72)


@router.post("/me/change-password")
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not _verify_password(body.currentPw, current_user.password_hash):
        raise AppError(401, "INVALID_CREDENTIALS", "현재 비밀번호가 올바르지 않습니다.")

    current_user.password_hash = _hash_password(body.newPw)
    db.commit()

    return {"success": True, "data": {"message": "비밀번호가 변경되었습니다."}}


# 마이페이지 알림 설정 (docs/fe/alert-settings-API-제안.md).
# 행이 없는 사용자는 화면 기본값으로 취급한다 — 회원가입 시 미리 만들 필요도,
# 조회 실패와 "아직 저장한 적 없음"을 구분할 필요도 없다.
_DEFAULT_ALERT_SETTING = {
    "emailFrequency": "daily",
    "deadlineAlertDays": 7,
    "deadlineDashboardAlert": True,
    "deadlineEmailAlert": False,
}


def _serialize_alert_setting(row: AlertSetting | None) -> dict:
    if row is None:
        return dict(_DEFAULT_ALERT_SETTING)
    return {
        "emailFrequency": row.email_frequency,
        "deadlineAlertDays": row.deadline_alert_days,
        "deadlineDashboardAlert": row.deadline_dashboard_alert,
        "deadlineEmailAlert": row.deadline_email_alert,
    }


@router.get("/me/alert-settings")
def get_alert_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.get(AlertSetting, current_user.id)
    return {"success": True, "data": _serialize_alert_setting(row)}


class UpdateAlertSettingsRequest(BaseModel):
    """4개 필드 전부(부분 수정이 아니라 전체 교체) — 화면 저장 버튼이 한 번에 다 보낸다."""
    emailFrequency: Literal["daily", "weekly"]
    deadlineAlertDays: Literal[7, 3, 1]
    deadlineDashboardAlert: bool
    deadlineEmailAlert: bool


@router.put("/me/alert-settings")
def update_alert_settings(
    body: UpdateAlertSettingsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.get(AlertSetting, current_user.id)
    if row is None:
        row = AlertSetting(user_id=current_user.id)
        db.add(row)

    row.email_frequency = body.emailFrequency
    row.deadline_alert_days = body.deadlineAlertDays
    row.deadline_dashboard_alert = body.deadlineDashboardAlert
    row.deadline_email_alert = body.deadlineEmailAlert
    db.commit()
    db.refresh(row)

    return {"success": True, "data": _serialize_alert_setting(row)}

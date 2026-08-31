"""
사원 인증 + 회원가입 + 로그인/로그아웃 (5주차 1차 작업 순서 4, 6)

FE(SignupPage.tsx/LoginPage.tsx)가 이미 쓰고 있는 필드명(empId, name, email, pw)을 그대로 API 필드명으로 사용합니다.

흐름:
  ① POST /auth/verify-employee : 사번+이름이 사원 명부에 있는지만 확인 (회원가입 1단계)
  ② POST /auth/signup          : ①을 통과한 사번에 한해 이메일/비밀번호로 계정 생성 (회원가입 2단계)
     POST /auth/login           : 사번+비밀번호 검증 후 로그인 토큰(JWT) 발급
     POST /auth/logout          : 상태를 안 가지는(stateless) JWT라 서버가 지울 게 없음 — FE가 토큰을 버리면 끝
"""
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import AppError
from app.db.models import Employee, User
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

JWT_ALGORITHM = "HS256"


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _find_employee(db: Session, emp_id: str, name: str) -> Employee | None:
    return db.execute(select(Employee).where(Employee.emp_id == emp_id, Employee.name == name)).scalar_one_or_none()


class VerifyEmployeeRequest(BaseModel):
    empId: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=50)


@router.post("/verify-employee")
def verify_employee(body: VerifyEmployeeRequest, db: Session = Depends(get_db)):
    """SignupPage의 '사원 정보 인증하기' 버튼이 호출. 데모 하드코딩(20230001/김민준)을 대체."""
    employee = _find_employee(db, body.empId, body.name)
    return {"success": True, "data": {"verified": employee is not None}}


class SignupRequest(BaseModel):
    empId: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    pw: str = Field(min_length=6, max_length=72)


@router.post("/signup")
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    # 회원가입 API 단독으로도 안전하도록 서버에서 사원 인증을 다시 한번 확인한다
    # (FE의 verify-employee 호출 결과만 믿지 않음 — 클라이언트 요청은 조작될 수 있음)
    employee = _find_employee(db, body.empId, body.name)
    if employee is None:
        raise AppError(400, "EMPLOYEE_NOT_FOUND", "사번과 이름이 일치하는 사원 정보를 찾을 수 없습니다.")

    if db.execute(select(User).where(User.emp_id == body.empId)).scalar_one_or_none() is not None:
        raise AppError(409, "DUPLICATE_EMP_ID", "이미 가입된 사번입니다.")

    if db.execute(select(User).where(User.email == body.email)).scalar_one_or_none() is not None:
        raise AppError(409, "DUPLICATE_EMAIL", "이미 등록된 이메일입니다.")

    user = User(emp_id=body.empId, email=body.email, password_hash=_hash_password(body.pw))
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"success": True, "data": {"id": str(user.id), "empId": user.emp_id, "email": user.email}}


class LoginRequest(BaseModel):
    empId: str
    pw: str


def _create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=JWT_ALGORITHM)


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.emp_id == body.empId)).scalar_one_or_none()
    if user is None or not _verify_password(body.pw, user.password_hash):
        raise AppError(401, "INVALID_CREDENTIALS", "사번 또는 비밀번호가 올바르지 않습니다.")

    token = _create_token(str(user.id))
    return {"success": True, "data": {"token": token, "id": str(user.id), "email": user.email}}


@router.post("/logout")
def logout():
    return {"success": True, "data": {"message": "로그아웃되었습니다."}}


def get_current_user(authorization: str | None = Header(None), db: Session = Depends(get_db)) -> User:
    """다른 라우터(키워드, 저장공고 등)에서 Depends(get_current_user)로 로그인 사용자를 확인할 때 사용.
    요청 헤더: Authorization: Bearer <login에서 받은 token>
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AppError(401, "UNAUTHORIZED", "로그인이 필요합니다.")

    token = authorization.removeprefix("Bearer ")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise AppError(401, "INVALID_TOKEN", "유효하지 않거나 만료된 토큰입니다.")

    # DB 전환 노트: PK가 CHAR(36) 문자열이라 uuid.UUID는 형식 검증·정규화용으로만 쓰고 str로 조회
    try:
        user_id = str(uuid.UUID(payload["sub"]))
    except (KeyError, ValueError):
        raise AppError(401, "INVALID_TOKEN", "유효하지 않거나 만료된 토큰입니다.")

    user = db.get(User, user_id)
    if user is None:
        raise AppError(401, "UNAUTHORIZED", "존재하지 않는 사용자입니다.")
    return user

"""관리자 전용 API (7주차 작업 순서 3)

users 계정은 본인이 이메일/비밀번호를 정하는 회원가입 절차로만 생성되므로,
관리자가 직접 만들 수 있는 건 사원 명부(employees) 등록뿐이다. 그래서 이 라우터는:
  - 사원 명부 관리: 등록(추가)해서 그 사번으로 본인이 회원가입할 수 있게 하고, 삭제(미가입 사원만)
  - 가입자(계정) 목록: 조회 + 삭제(=접근 차단, 로그인 불가)
두 가지를 다룬다. 모든 엔드포인트는 Depends(get_current_admin) — 비관리자는 403.
"""
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_admin
from app.core.errors import AppError
from app.db.models import Employee, User
from app.db.session import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


def _serialize_employee(row: Employee, joined: bool) -> dict:
    return {
        "empId": row.emp_id,
        "name": row.name,
        "department": row.department,
        "createdAt": row.created_at,
        "joined": joined,
    }


@router.get("/employees")
def list_employees(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    joined_subq = select(User.emp_id).where(User.emp_id == Employee.emp_id)
    stmt = select(Employee, exists(joined_subq)).order_by(Employee.created_at.desc())
    rows = db.execute(stmt).all()
    return {"success": True, "data": [_serialize_employee(row, joined) for row, joined in rows]}


class EmployeeCreateRequest(BaseModel):
    empId: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=50)
    department: str | None = Field(default=None, max_length=100)


@router.post("/employees")
def create_employee(
    body: EmployeeCreateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    if db.get(Employee, body.empId) is not None:
        raise AppError(409, "DUPLICATE_EMP_ID", "이미 등록된 사번입니다.")

    row = Employee(emp_id=body.empId, name=body.name, department=body.department)
    db.add(row)
    db.commit()
    db.refresh(row)

    return {"success": True, "data": _serialize_employee(row, joined=False)}


@router.delete("/employees/{emp_id}")
def delete_employee(
    emp_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    row = db.get(Employee, emp_id)
    if row is None:
        raise AppError(404, "EMPLOYEE_NOT_FOUND", "존재하지 않는 사원입니다.")

    joined = db.execute(select(User).where(User.emp_id == emp_id)).scalar_one_or_none() is not None
    if joined:
        raise AppError(409, "EMPLOYEE_ALREADY_JOINED", "이미 가입한 사원은 명부에서 삭제할 수 없습니다.")

    db.delete(row)
    db.commit()

    return {"success": True, "data": {"message": "사원 명부에서 삭제되었습니다."}}


def _serialize_user(user: User, employee: Employee) -> dict:
    return {
        "id": str(user.id),
        "empId": user.emp_id,
        "name": employee.name,
        "department": employee.department,
        "email": user.email,
        "isAdmin": user.is_admin,
        "createdAt": user.created_at,
    }


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    stmt = (
        select(User, Employee)
        .join(Employee, Employee.emp_id == User.emp_id)
        .order_by(User.created_at.desc())
    )
    rows = db.execute(stmt).all()
    return {"success": True, "data": [_serialize_user(user, employee) for user, employee in rows]}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    try:
        parsed_id = str(uuid.UUID(user_id))  # CHAR(36) PK — 형식 검증 후 문자열로 조회
    except ValueError:
        raise AppError(404, "USER_NOT_FOUND", "존재하지 않는 가입자입니다.")

    row = db.get(User, parsed_id)
    if row is None:
        raise AppError(404, "USER_NOT_FOUND", "존재하지 않는 가입자입니다.")

    db.delete(row)
    db.commit()

    return {"success": True, "data": {"message": "가입자 계정이 삭제되었습니다."}}

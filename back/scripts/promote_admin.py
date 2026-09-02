"""최초 관리자 지정용 1회성 스크립트.

사용법 (back/ 에서 실행):
    .venv\\Scripts\\python scripts\\promote_admin.py <emp_id>

해당 사번으로 이미 회원가입한 계정의 is_admin을 True로 바꿉니다.
이후 관리자 추가는 이 스크립트가 아니라 관리자 화면(사원 명부 등록 → 본인 회원가입)으로 처리합니다.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.db.models import User  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402


def main(emp_id: str) -> None:
    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.emp_id == emp_id)).scalar_one_or_none()
        if user is None:
            print(f"사번 {emp_id}로 가입한 계정이 없습니다. 먼저 회원가입을 완료하세요.")
            return
        if user.is_admin:
            print(f"{emp_id} ({user.email})은(는) 이미 관리자입니다.")
            return
        user.is_admin = True
        db.commit()
        print(f"{emp_id} ({user.email}) 계정을 관리자로 지정했습니다.")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용법: python scripts/promote_admin.py <emp_id>")
        sys.exit(1)
    main(sys.argv[1])

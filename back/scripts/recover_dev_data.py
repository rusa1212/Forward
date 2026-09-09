"""로컬 개발 DB 복구용 1회성 스크립트.

전체 pytest 스위트가 conftest.py의 clean_db fixture로 .env가 가리키는 DB의
employees/users/announcements/keywords/saved_announcements/notification_logs를
비운 뒤 복구할 때 사용합니다.

하는 일:
  1. dev-seed.sql과 동일한 데모 사원(20230001 김민준) 재삽입
  2. 공공데이터포털 3개 소스에서 공고를 다시 수집해 announcements에 저장
  3. 삭제된 사용자를 가리키는 고아 alert_settings 행 정리

user / keyword / saved_announcements는 앱에서 직접 만든 데이터라 이 스크립트로는
복구되지 않습니다 — 재가입 후 다시 등록해야 합니다.

사용법 (back/ 에서 실행):
    .venv\\Scripts\\python scripts\\recover_dev_data.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.db.models import Employee  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.services.collector import collect_all, today_bid_date_range  # noqa: E402
from app.services.storage import save_announcements  # noqa: E402

_SEED_EMPLOYEES = [
    ("20230001", "김민준", "개발팀"),
]


def seed_employees(db) -> None:
    for emp_id, name, department in _SEED_EMPLOYEES:
        if db.get(Employee, emp_id) is None:
            db.add(Employee(emp_id=emp_id, name=name, department=department))
    db.commit()
    print(f"employees: 데모 사원 {len(_SEED_EMPLOYEES)}명 확인/삽입")


def clean_orphan_alert_settings(db) -> None:
    deleted = db.execute(
        text("DELETE FROM alert_settings WHERE user_id NOT IN (SELECT id FROM users)")
    ).rowcount
    db.commit()
    print(f"alert_settings: 고아 행 {deleted}건 삭제")


async def recollect(db) -> None:
    bgn, end = today_bid_date_range()
    result = await collect_all(bgn, end)
    counts = {source: len(items) for source, items in result.items()}
    all_items = [item for items in result.values() for item in items]
    saved = save_announcements(db, all_items)
    print(f"announcements: fetched={counts} saved={saved}")


def main() -> None:
    db = SessionLocal()
    try:
        seed_employees(db)
        clean_orphan_alert_settings(db)
        asyncio.run(recollect(db))

        print("\n현재 행 수:")
        for table in ("employees", "users", "announcements", "keywords", "saved_announcements", "alert_settings"):
            n = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"  {table:24} {n}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

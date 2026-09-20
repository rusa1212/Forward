"""보관 기간이 지난 마감 공고를 DB에서 정리하는 스크립트.

평소에는 수집 사이클이 매번 알아서 정리한다(app/services/collect_cycle.py).
이 스크립트는 그 자동 정리를 기다리지 않고 지금 돌리거나, 기간을 따로 지정해서
한 번만 정리하고 싶을 때 쓴다.

사용법 (back/ 에서 실행):
    .venv\\Scripts\\python scripts\\purge_old_announcements.py              # 미리보기(기본)
    .venv\\Scripts\\python scripts\\purge_old_announcements.py --apply      # 실제 삭제
    .venv\\Scripts\\python scripts\\purge_old_announcements.py --days 60 --apply

기본은 **미리보기**다 — 몇 건이 지워질지만 출력하고 DB는 건드리지 않는다.
실제로 지우려면 --apply를 붙여야 한다.

--include-saved 는 사용자가 저장(즐겨찾기)한 공고까지 같이 지운다. FK가 CASCADE라
마이페이지의 저장 목록에서도 함께 사라지므로 정말 필요한 경우에만 쓸 것.
알림 이력은 어느 쪽이든 남는다 (FK가 ON DELETE SET NULL — 링크만 끊긴다).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal  # noqa: E402
from app.services.collector import RECENT_CLOSED_DAYS  # noqa: E402
from app.services.storage import purge_stale_closed_announcements  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="보관 기간이 지난 마감 공고 정리")
    parser.add_argument(
        "--days",
        type=int,
        default=RECENT_CLOSED_DAYS,
        help=f"마감 후 보관할 일수 (기본: 수집기와 같은 {RECENT_CLOSED_DAYS}일)",
    )
    parser.add_argument("--apply", action="store_true", help="실제로 삭제한다 (없으면 미리보기)")
    parser.add_argument(
        "--include-saved",
        action="store_true",
        help="사용자가 저장(즐겨찾기)한 공고까지 삭제 (CASCADE로 저장 목록에서도 사라짐)",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        result = purge_stale_closed_announcements(
            db,
            days=args.days,
            keep_saved=not args.include_saved,
            dry_run=not args.apply,
        )
    finally:
        db.close()

    mode = "삭제 완료" if args.apply else "미리보기 (실제 삭제 안 함)"
    print(f"[{mode}] 기준: {result['cutoff']} 이전 마감 ({args.days}일 경과)")
    print(f"  대상 공고      : {result['matched']}건")
    print(f"  {'지운 공고     ' if args.apply else '지울 공고     '} : {result['deleted']}건")
    if not args.include_saved:
        print(f"  건너뛴 공고    : {result['kept_saved']}건 (사용자가 저장한 공고)")
    if not args.apply and result["deleted"]:
        print("\n실제로 지우려면 --apply 를 붙여 다시 실행하세요.")


if __name__ == "__main__":
    main()

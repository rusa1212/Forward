"""로깅 설정 (5주차 우선순위 "예외/로그 보강").

main.py가 앱을 만들기 전에 가장 먼저 setup_logging()을 호출한다.

이전에는 아무도 logging.basicConfig()를 호출하지 않았다. 파이썬 로깅은 핸들러가
하나도 설정되어 있지 않으면 WARNING 이상만 "최후의 수단(handler of last resort)"으로
stderr에 찍고, 그 밑 레벨(INFO 등)은 조용히 버린다. 그래서 scheduler.py/notifier.py가
logger.info(...)로 남기던 "자동 수집 몇 건, 알림 몇 건 생성/발송" 같은 로그가 실제로는
어디에도 출력되지 않고 있었다 — 이 함수가 그 부분을 고쳐서 INFO 레벨 로그도 보이게 한다.
"""
import logging


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # apscheduler는 job 스케줄링 내부 동작까지 INFO로 꽤 시끄럽게 찍어서 WARNING으로만 올려둠
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

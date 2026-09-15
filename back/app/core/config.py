"""환경변수 설정 (.env 에서 읽어옵니다)"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "forward-be"
    ENV: str = "local"  # local / dev / prod

    # FE 주소 (CORS 허용). 쉼표로 여러 개 지정할 수 있다 —
    # 배포 후에는 "운영 주소 + 로컬 개발 주소"를 같이 열어두는 경우가 많다.
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    # 주소가 배포마다 바뀌는 오리진을 정규식으로 허용한다. Vercel 프리뷰 배포가 그런 경우로,
    # 운영 주소 하나만 열어두면 PR 미리보기에서 API 호출이 전부 CORS로 막힌다.
    # 예: https://forward-.*-myteam\.vercel\.app  (비워두면 정규식 허용 없음)
    FRONTEND_ORIGIN_REGEX: str = ""

    # 공공데이터포털 발급 API 키 (4개 서비스 공용)
    DATA_GO_KR_API_KEY: str = ""

    # DB 접속정보 (MySQL/MariaDB, mysql+pymysql://... 형식 — .env.example 참고)
    DATABASE_URL: str = ""

    # pytest 전용 DB. 비워두면 DATABASE_URL의 DB 이름 뒤에 "_test"를 붙여서 쓴다
    # (예: forward -> forward_test). 테스트는 이 DB를 매 실행마다 드롭/재생성하므로
    # 절대 DATABASE_URL과 같은 DB를 가리키면 안 된다 (conftest.py가 같으면 실행을 막는다).
    TEST_DATABASE_URL: str = ""

    # 자동 수집 실행 시각 (서버 로컬 시간 기준). 쉼표로 여러 시각 지정 — 기본은 하루 2회(06시·18시).
    # APScheduler CronTrigger의 hour 필드에 그대로 전달된다 ("6,18", "0,6,12,18", "*/6" 등).
    COLLECT_CRON_HOURS: str = "6,18"
    COLLECT_CRON_MINUTE: int = 0

    # 외부 cron(cron-job.org 등)이 POST /api/v1/collect/cron 을 호출할 때 쓰는 고정 토큰.
    # 관리자 JWT는 24시간이면 만료돼 cron에 넣어둘 수 없어서 별도로 둔다.
    # 비워두면(기본) 그 엔드포인트가 404로 완전히 닫힌다 — 토큰을 안 정한 채 배포해도
    # 아무나 수집을 트리거할 수 있는 구멍이 생기지 않도록.
    CRON_TOKEN: str = ""

    # 로그인 토큰(JWT) 서명용. 실서비스 배포 전 반드시 각자 .env에서 무작위 값으로 교체할 것.
    JWT_SECRET: str = "change-me-in-env"
    JWT_EXPIRE_HOURS: int = 24

    # 알림 이메일 발송용 SMTP (app/services/notifier.py). SMTP_HOST가 비어있으면(기본값)
    # 이메일 발송 없이 알림 저장만 하고 넘어간다 — 어떤 이메일 서비스를 쓸지 아직 팀 결정 전이라
    # 안전한 기본값으로 꺼둔 상태. 결정되면 .env에 값만 채우면 됨(코드 수정 불필요).
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True

    @property
    def frontend_origins(self) -> list[str]:
        """FRONTEND_ORIGIN(쉼표 구분)을 CORS 미들웨어가 받는 리스트로 변환."""
        return [origin.strip() for origin in self.FRONTEND_ORIGIN.split(",") if origin.strip()]


settings = Settings()

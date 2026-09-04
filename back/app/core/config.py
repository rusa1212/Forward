"""환경변수 설정 (.env 에서 읽어옵니다)"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "forward-be"
    ENV: str = "local"  # local / dev / prod

    # FE 개발 서버 주소 (CORS 허용)
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    # 공공데이터포털 발급 API 키 (4개 서비스 공용)
    DATA_GO_KR_API_KEY: str = ""

    # DB 접속정보 (MySQL/MariaDB, mysql+pymysql://... 형식 — .env.example 참고)
    DATABASE_URL: str = ""

    # 매일 자동 수집 실행 시각 (서버 로컬 시간 기준)
    COLLECT_CRON_HOUR: int = 6
    COLLECT_CRON_MINUTE: int = 0

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


settings = Settings()

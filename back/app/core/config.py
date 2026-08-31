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


settings = Settings()

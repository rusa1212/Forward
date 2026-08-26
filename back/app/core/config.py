"""
환경변수 설정 (WBS 1.1)

.env 파일에서 값을 읽어옵니다. DB 담당 팀원에게 .env를 받으면
이 파일은 손댈 필요 없이 그대로 DATABASE_URL만 읽어서 씁니다.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "forward-be"
    ENV: str = "local"  # local / dev / prod

    # DB 팀원이 .env로 넘겨줄 값. 아직 없으면 로컬 기본값으로 동작(서버는 뜨지만 DB 붙는 API는 에러).
    DATABASE_URL: str = "postgresql+psycopg2://forward_dev:forward_dev_pw@localhost/forward_dev"

    # FE 개발 서버 주소 (CORS 허용). React 기본 포트 기준.
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    # 인증
    JWT_SECRET: str = "change-me-in-env"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24


settings = Settings()

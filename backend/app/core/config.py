from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    UPLOAD_DIR: str = "/app/uploads"
    WXWORK_WEBHOOK_URL: str = ""  # 企业微信群机器人 Webhook，留空则不推送

    class Config:
        env_file = ".env"


settings = Settings()

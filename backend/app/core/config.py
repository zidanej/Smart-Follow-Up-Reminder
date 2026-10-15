from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/reminders.db"
    backend_url: str = "http://127.0.0.1:8000"
    app_env: str = "development"
    enable_scheduler: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

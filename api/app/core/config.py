from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    debug: bool = True

    # Logging settings
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

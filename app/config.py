from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://klepak:klepak_dev@localhost:5432/klepak_scores"

    model_config = {"env_file": ".env"}


settings = Settings()

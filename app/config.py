from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://klepak:klepak_dev@localhost:5432/klepak_scores"
    SECRET_KEY: str  # no default — raises ValidationError at startup if missing
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # SMTP settings (empty = dev mode, prints to console)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_USE_TLS: bool = True       # STARTTLS on port 587
    SMTP_USE_SSL: bool = False      # Implicit SSL on port 465

    FRONTEND_URL: str = "http://localhost:4200"
    PASSWORD_RESET_EXPIRE_MINUTES: int = 60

    SUPER_ADMIN_EMAIL: str = ""
    INVITATION_EXPIRE_DAYS: int = 7
    BOOTSTRAP_TOKEN_EXPIRE_HOURS: int = 48

    model_config = {"env_file": ".env"}


settings = Settings()

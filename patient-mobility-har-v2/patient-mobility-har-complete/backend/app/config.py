"""
Centralized application configuration.

All environment-dependent values are loaded and validated here, once,
through a Pydantic Settings class. Every other module imports `settings`
from this file instead of reading `os.environ` directly.
"""

from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Application ---
    APP_NAME: str = "Patient Mobility HAR System"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./patient_mobility.db"

    # --- Authentication / JWT ---
    SECRET_KEY: str = "change_this_to_a_long_random_secret_string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Default admin account ---
    DEFAULT_ADMIN_NAME: str = "System Administrator"
    DEFAULT_ADMIN_EMAIL: str = "admin@example.com"
    DEFAULT_ADMIN_PASSWORD: str = "ChangeMe123!"

    # --- CORS ---
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # --- File storage ---
    UPLOAD_DIR: str = "./uploads"
    MODELS_DIR: str = "./models_store"

    # --- Camera defaults ---
    DEFAULT_CAMERA_SOURCE: str = "0"
    CAMERA_TARGET_FPS: int = 15

    # --- Detection thresholds ---
    FALL_TORSO_ANGLE_THRESHOLD_DEG: float = 55.0
    FALL_VERTICAL_VELOCITY_THRESHOLD: float = 0.35
    FALL_CONFIRMATION_WINDOW_SEC: float = 5.0
    INACTIVITY_THRESHOLD_SEC: float = 60.0
    ACTIVITY_CONFIDENCE_MIN: float = 0.60

    # --- Activity-recognition temporal smoothing (see app/ml/activity_smoother.py) ---
    ACTIVITY_SMOOTHING_WINDOW_SEC: float = 1.0
    ACTIVITY_SWITCH_MARGIN: float = 0.10

    # --- Email (SMTP) ---
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "Patient Monitoring Alerts"
    ALERT_RECIPIENT_EMAIL: str = ""

    # --- Telegram (optional) ---
    TELEGRAM_ENABLED: bool = False
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # --- SMS/voice-call alerts (optional, real provider only — Twilio) ---
    # Leave blank to disable. When blank, sms_notifier.py no-ops with a
    # logged warning and never reports a fake successful send. Requires
    # the `twilio` package (see requirements.txt) and a real Twilio
    # account; no other provider is currently wired in.
    SMS_ENABLED: bool = False
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""
    TWILIO_WHATSAPP_FROM: str = ""
    ALERT_RECIPIENT_WHATSAPP: str = ""
    SMS_CALL_ON_CRITICAL_ALERT: bool = False  # place a voice call (not just SMS) for critical alerts

    # --- Logging ---
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def upload_path(self) -> Path:
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def models_path(self) -> Path:
        path = Path(self.MODELS_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def log_path(self) -> Path:
        path = Path(self.LOG_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    """Returns a cached Settings instance so the .env file is parsed once."""
    return Settings()


settings = get_settings()

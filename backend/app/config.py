"""Application configuration loaded from environment variables."""
import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./pricedrop.db"))
    telegram_bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))
    drop_threshold_pct: float = field(default_factory=lambda: float(os.getenv("DROP_THRESHOLD_PCT", "5")))

    # Shopee Affiliate Open API (AMS)
    shopee_app_id: str = field(default_factory=lambda: os.getenv("SHOPEE_APP_ID", ""))
    shopee_app_secret: str = field(default_factory=lambda: os.getenv("SHOPEE_APP_SECRET", ""))
    shopee_partner_id: str = field(default_factory=lambda: os.getenv("SHOPEE_PARTNER_ID", ""))

    # TikTok Shop Affiliate API
    tiktok_app_key: str = field(default_factory=lambda: os.getenv("TIKTOK_APP_KEY", ""))
    tiktok_app_secret: str = field(default_factory=lambda: os.getenv("TIKTOK_APP_SECRET", ""))
    tiktok_shop_id: str = field(default_factory=lambda: os.getenv("TIKTOK_SHOP_ID", ""))

    # Background checker
    checker_enabled: bool = field(default_factory=lambda: os.getenv("CHECKER_ENABLED", "true").lower() == "true")
    checker_interval_seconds: int = field(
        default_factory=lambda: int(os.getenv("CHECKER_INTERVAL_SECONDS", "21600"))
    )

    # Security
    api_key: str = field(default_factory=lambda: os.getenv("API_KEY", ""))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    cors_origins: str = field(default_factory=lambda: os.getenv("CORS_ORIGINS", "*"))

    def __post_init__(self):
        self.drop_threshold_pct = float(self.drop_threshold_pct)


settings = Settings()

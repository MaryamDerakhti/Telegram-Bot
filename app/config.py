from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    admin_ids: str = ""
    database_url: str = "sqlite+aiosqlite:///./bot.db"
    bot_username: str
    free_daily_limit: int = 5
    vip_daily_limit: int = 50
    report_suspend_threshold: int = 5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def admin_id_set(self) -> set[int]:
        return {
            int(value.strip())
            for value in self.admin_ids.split(",")
            if value.strip().isdigit()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()

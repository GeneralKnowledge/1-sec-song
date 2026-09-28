from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_secret_key: str = Field(alias="APP_SECRET_KEY")
    itunes_search_terms: str = Field(
        default=(
            "pop hits,rock classics,hip hop,r&b,indie pop,"
            "taylor swift,the weeknd,drake,billie eilish,coldplay"
        ),
        alias="ITUNES_SEARCH_TERMS",
        description="Comma-separated iTunes search terms used to build the track pool",
    )
    itunes_country: str = Field(default="us", alias="ITUNES_COUNTRY")
    itunes_search_limit: int = Field(default=25, alias="ITUNES_SEARCH_LIMIT")
    track_cache_ttl_seconds: int = Field(default=3600, alias="TRACK_CACHE_TTL_SECONDS")
    sqlite_path: str = Field(default="./track_cache.db", alias="SQLITE_PATH")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def search_terms(self) -> List[str]:
        return [term.strip() for term in self.itunes_search_terms.split(",") if term.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

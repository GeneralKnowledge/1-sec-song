from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    spotify_client_id: str = Field(alias="SPOTIFY_CLIENT_ID")
    spotify_client_secret: str = Field(alias="SPOTIFY_CLIENT_SECRET")
    app_secret_key: str = Field(alias="APP_SECRET_KEY")
    spotify_playlist_ids: str = Field(
        default="37i9dQZF1DXcBWIGoYBM5M",
        alias="SPOTIFY_PLAYLIST_IDS",
        description="Comma-separated Spotify playlist IDs",
    )
    track_cache_ttl_seconds: int = Field(default=3600, alias="TRACK_CACHE_TTL_SECONDS")
    sqlite_path: str = Field(default="./track_cache.db", alias="SQLITE_PATH")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @property
    def playlist_ids(self) -> List[str]:
        return [playlist_id.strip() for playlist_id in self.spotify_playlist_ids.split(",") if playlist_id.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

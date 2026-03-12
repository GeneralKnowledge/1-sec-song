import time
from typing import Any, List

import httpx

from app.config import Settings
from app.schemas import Track


class SpotifyClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    async def _ensure_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 30:
            return self._access_token

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "https://accounts.spotify.com/api/token",
                data={"grant_type": "client_credentials"},
                auth=(self.settings.spotify_client_id, self.settings.spotify_client_secret),
            )
            response.raise_for_status()
            payload = response.json()

        self._access_token = payload["access_token"]
        self._token_expires_at = time.time() + payload.get("expires_in", 3600)
        return self._access_token

    async def _get_playlist_tracks(self, playlist_id: str) -> List[dict[str, Any]]:
        token = await self._ensure_token()
        headers = {"Authorization": f"Bearer {token}"}
        items: List[dict[str, Any]] = []
        next_url = (
            f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
            "?fields=next,items(track(id,name,preview_url,artists(name),album(images)))&limit=100"
        )

        async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
            while next_url:
                response = await client.get(next_url)
                response.raise_for_status()
                payload = response.json()
                items.extend(payload.get("items", []))
                next_url = payload.get("next")

        return items

    async def get_curated_tracks(self) -> List[Track]:
        seen: set[str] = set()
        tracks: List[Track] = []

        for playlist_id in self.settings.playlist_ids:
            playlist_items = await self._get_playlist_tracks(playlist_id)
            for item in playlist_items:
                track_data = item.get("track") or {}
                preview_url = track_data.get("preview_url")
                track_id = track_data.get("id")
                title = track_data.get("name")
                artists = track_data.get("artists") or []
                artist_name = artists[0].get("name") if artists else "Unknown Artist"
                images = (track_data.get("album") or {}).get("images") or []
                image_url = images[0].get("url") if images else None

                if not preview_url or not track_id or not title or track_id in seen:
                    continue

                seen.add(track_id)
                tracks.append(
                    Track(
                        track_id=track_id,
                        title=title,
                        artist=artist_name,
                        preview_url=preview_url,
                        image_url=image_url,
                    )
                )

        return tracks

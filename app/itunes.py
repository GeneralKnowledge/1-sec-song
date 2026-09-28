from typing import Any, List
from urllib.parse import quote_plus

import httpx

from app.config import Settings
from app.schemas import Track


class ITunesClient:
    SEARCH_URL = "https://itunes.apple.com/search"

    def __init__(self, settings: Settings):
        self.settings = settings

    @staticmethod
    def _upgrade_artwork(url: str | None) -> str | None:
        if not url:
            return None
        return url.replace("100x100bb", "600x600bb")

    async def _search_songs(self, term: str) -> List[dict[str, Any]]:
        params = {
            "term": term,
            "media": "music",
            "entity": "song",
            "limit": self.settings.itunes_search_limit,
            "country": self.settings.itunes_country,
        }
        # quote_plus keeps spaces as +, which matches iTunes Search docs.
        query = "&".join(f"{key}={quote_plus(str(value))}" for key, value in params.items())
        url = f"{self.SEARCH_URL}?{query}"

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            payload = response.json()

        return payload.get("results") or []

    async def get_curated_tracks(self) -> List[Track]:
        seen: set[str] = set()
        tracks: List[Track] = []

        for term in self.settings.search_terms:
            results = await self._search_songs(term)
            for item in results:
                preview_url = item.get("previewUrl")
                track_id = item.get("trackId")
                title = item.get("trackName")
                artist_name = item.get("artistName") or "Unknown Artist"
                image_url = self._upgrade_artwork(item.get("artworkUrl100"))

                if not preview_url or not track_id or not title:
                    continue

                track_id_str = str(track_id)
                if track_id_str in seen:
                    continue

                seen.add(track_id_str)
                tracks.append(
                    Track(
                        track_id=track_id_str,
                        title=title,
                        artist=artist_name,
                        preview_url=preview_url,
                        image_url=image_url,
                    )
                )

        return tracks

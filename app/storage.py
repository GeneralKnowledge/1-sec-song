import json
import sqlite3
import time
from pathlib import Path
from typing import List

from app.schemas import Track


class TrackCache:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_meta (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    updated_at INTEGER NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tracks (
                    track_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )

    def get_tracks_if_fresh(self, ttl_seconds: int) -> List[Track] | None:
        now = int(time.time())
        with self._connect() as conn:
            row = conn.execute("SELECT updated_at FROM cache_meta WHERE id = 1").fetchone()
            if not row:
                return None
            if now - row["updated_at"] > ttl_seconds:
                return None
            track_rows = conn.execute("SELECT payload FROM tracks").fetchall()

        if not track_rows:
            return None
        return [Track(**json.loads(track_row["payload"])) for track_row in track_rows]

    def save_tracks(self, tracks: List[Track]) -> None:
        now = int(time.time())
        with self._connect() as conn:
            conn.execute("DELETE FROM tracks")
            conn.executemany(
                "INSERT INTO tracks(track_id, payload) VALUES(?, ?)",
                [(track.track_id, track.model_dump_json()) for track in tracks],
            )
            conn.execute(
                "INSERT INTO cache_meta(id, updated_at) VALUES(1, ?) "
                "ON CONFLICT(id) DO UPDATE SET updated_at = excluded.updated_at",
                (now,),
            )

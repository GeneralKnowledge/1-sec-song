import random
import uuid
from dataclasses import dataclass
from typing import List

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.schemas import Choice, GuessResponse, RoundResponse, Track


@dataclass
class ScoreState:
    score: int = 0
    streak: int = 0


class GameService:
    def __init__(self, secret_key: str):
        self.serializer = URLSafeTimedSerializer(secret_key=secret_key, salt="round-token")

    @staticmethod
    def choose_clip_start_ms(min_ms: int = 2000, max_ms: int = 27000) -> int:
        return random.randint(min_ms, max_ms)

    def build_round(self, tracks: List[Track]) -> RoundResponse:
        if len(tracks) < 4:
            raise ValueError("Not enough tracks with preview URLs. Need at least 4.")

        correct_track = random.choice(tracks)
        distractors = random.sample([t for t in tracks if t.track_id != correct_track.track_id], 3)
        options = [correct_track.title] + [track.title for track in distractors]
        random.shuffle(options)

        round_id = str(uuid.uuid4())
        payload = {
            "round_id": round_id,
            "correct_title": correct_track.title,
            "artist": correct_track.artist,
        }
        token = self.serializer.dumps(payload)

        return RoundResponse(
            round_id=round_id,
            token=token,
            preview_url=correct_track.preview_url,
            start_ms=self.choose_clip_start_ms(),
            choices=[Choice(title=option) for option in options],
        )

    def check_guess(self, round_id: str, token: str, selected_choice: str, score_state: ScoreState) -> GuessResponse:
        try:
            payload = self.serializer.loads(token, max_age=600)
        except SignatureExpired as exc:
            raise ValueError("Round expired. Please start a new round.") from exc
        except BadSignature as exc:
            raise ValueError("Invalid round token.") from exc

        if payload.get("round_id") != round_id:
            raise ValueError("Round mismatch. Please start a new round.")

        correct_answer = payload["correct_title"]
        artist = payload["artist"]
        correct = selected_choice == correct_answer

        if correct:
            score_state.score += 1
            score_state.streak += 1
        else:
            score_state.streak = 0

        return GuessResponse(
            correct=correct,
            correct_answer=correct_answer,
            artist=artist,
            score=score_state.score,
            streak=score_state.streak,
        )

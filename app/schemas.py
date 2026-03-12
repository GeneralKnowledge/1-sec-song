from typing import List

from pydantic import BaseModel, HttpUrl


class Track(BaseModel):
    track_id: str
    title: str
    artist: str
    preview_url: HttpUrl
    image_url: HttpUrl | None = None


class Choice(BaseModel):
    title: str


class RoundResponse(BaseModel):
    round_id: str
    token: str
    preview_url: HttpUrl
    start_ms: int
    duration_ms: int = 1000
    choices: List[Choice]


class GuessRequest(BaseModel):
    round_id: str
    token: str
    selected_choice: str


class GuessResponse(BaseModel):
    correct: bool
    correct_answer: str
    artist: str
    score: int
    streak: int


class ErrorResponse(BaseModel):
    detail: str

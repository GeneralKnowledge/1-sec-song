from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.config import Settings, get_settings
from app.game import GameService, ScoreState
from app.schemas import GuessRequest, GuessResponse, RoundResponse, Track
from app.spotify import SpotifyClient
from app.storage import TrackCache

BASE_DIR = Path(__file__).resolve().parent
settings = get_settings()

app = FastAPI(title="1-Second Song Quiz")
app.add_middleware(SessionMiddleware, secret_key=settings.app_secret_key, max_age=60 * 60 * 24 * 7)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.on_event("startup")
async def startup_event() -> None:
    app.state.settings = settings
    app.state.spotify_client = SpotifyClient(settings)
    app.state.track_cache = TrackCache(settings.sqlite_path)
    app.state.game_service = GameService(settings.app_secret_key)


async def get_track_pool(request: Request) -> list[Track]:
    settings_obj: Settings = request.app.state.settings
    cache: TrackCache = request.app.state.track_cache
    spotify_client: SpotifyClient = request.app.state.spotify_client

    cached_tracks = cache.get_tracks_if_fresh(settings_obj.track_cache_ttl_seconds)
    if cached_tracks:
        return cached_tracks

    tracks = await spotify_client.get_curated_tracks()
    if not tracks:
        raise HTTPException(status_code=503, detail="No playable tracks found. Check Spotify credentials/playlists.")
    cache.save_tracks(tracks)
    return tracks


def get_score_state(request: Request) -> ScoreState:
    score = request.session.get("score", 0)
    streak = request.session.get("streak", 0)
    return ScoreState(score=score, streak=streak)


def save_score_state(request: Request, state: ScoreState) -> None:
    request.session["score"] = state.score
    request.session["streak"] = state.streak


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/round", response_model=RoundResponse)
async def new_round(request: Request, tracks: list[Track] = Depends(get_track_pool)) -> RoundResponse:
    game_service: GameService = request.app.state.game_service
    try:
        return game_service.build_round(tracks)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/guess", response_model=GuessResponse)
async def submit_guess(request: Request, payload: GuessRequest) -> GuessResponse:
    game_service: GameService = request.app.state.game_service
    score_state = get_score_state(request)

    try:
        result = game_service.check_guess(
            round_id=payload.round_id,
            token=payload.token,
            selected_choice=payload.selected_choice,
            score_state=score_state,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    save_score_state(request, score_state)
    return result


@app.get("/api/state")
async def get_state(request: Request) -> dict[str, int]:
    state = get_score_state(request)
    return {"score": state.score, "streak": state.streak}

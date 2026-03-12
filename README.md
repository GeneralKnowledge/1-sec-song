# 1-Second Song Quiz (FastAPI MVP)

A simple web MVP where players hear exactly **1 second** of a Spotify preview clip and guess the song from four options.

## Stack
- Python 3.12
- FastAPI + Uvicorn
- Vanilla HTML/CSS/JavaScript
- Spotify Web API (Client Credentials flow)
- SQLite (lightweight metadata cache)

## Features
- Generates quiz rounds from curated Spotify playlists.
- Uses only Spotify `preview_url` streams (no audio file download/storage).
- Filters out tracks without `preview_url`.
- Plays a random 1-second segment (`2000ms` to `27000ms`).
- Multiple-choice mode with 4 options.
- Secure round validation with signed token.
- Score and streak tracking per browser session.
- Next-round flow.

## Project structure

```
app/
  main.py
  config.py
  spotify.py
  game.py
  schemas.py
  storage.py
  templates/index.html
  static/styles.css
  static/app.js
scripts/
  bootstrap_and_check.sh
requirements.txt
.env.example
README.md
```

## Spotify setup
1. Create a Spotify app in the Spotify Developer Dashboard.
2. Copy your credentials:
   - `SPOTIFY_CLIENT_ID`
   - `SPOTIFY_CLIENT_SECRET`
3. Choose one or more Spotify playlist IDs and set `SPOTIFY_PLAYLIST_IDS` as comma-separated values.

## Local setup (recommended)

Use the helper script for a consistent Python 3.12 virtualenv setup:

```bash
./scripts/bootstrap_and_check.sh
cp .env.example .env
```

Then run:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Open: http://127.0.0.1:8000

## Manual setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

> Note: On Debian/Ubuntu, `python3.12 -m pip` may fail on system Python because pip is disabled there. Using a virtual environment (`python3.12 -m venv .venv`) solves this.

## Restricted-network / proxy environments

If package installs fail because outbound access is blocked, point pip to your internal package index:

```bash
source .venv/bin/activate
PIP_INDEX_URL=http://<your-internal-pypi>/simple \
python -m pip install --trusted-host <your-internal-pypi-host> -r requirements.txt
```

## API overview
- `GET /api/round`
  - Returns `round_id`, signed `token`, `preview_url`, `start_ms`, `duration_ms`, and 4 shuffled choices.
  - Correct answer is hidden from the response.

- `POST /api/guess`
  - Input: `round_id`, `token`, `selected_choice`
  - Validates token + round integrity
  - Returns correctness, answer reveal, artist, score, streak

- `GET /api/state`
  - Returns current browser session score/streak.

## Security notes
- Round answer data is signed server-side using `APP_SECRET_KEY`.
- Token tampering or expired rounds are rejected.
- Session cookie stores score/streak only.

## Architecture (short)
- **FastAPI backend** serves UI and JSON API.
- **Spotify client module** fetches playlist tracks via Client Credentials flow.
- **SQLite cache layer** stores track metadata (ID/title/artist/preview URL/image URL).
- **Game service** creates rounds, signs hidden answer data, validates guesses, updates score/streak.
- **Vanilla JS frontend** handles round lifecycle, 1-second playback, guessing, and rendering feedback.

## Next improvements
- Daily challenge mode with fixed seed.
- Categories by genre/mood/decade.
- Global leaderboards + user accounts.
- Timed mode and bonus points.
- Better anti-cheat telemetry and analytics.
- Accessibility upgrades (keyboard flow, ARIA live regions).

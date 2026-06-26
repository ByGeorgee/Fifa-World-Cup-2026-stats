"""Static configuration for the FIFA 2026 backend."""
import os
from pathlib import Path

# results_data/ lives at the repository root: backend/app/config.py -> parents[2] == repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "results_data"


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader: KEY=VALUE per line, '#' comments, no override of real env vars."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv(REPO_ROOT / ".env")

# ESPN public, key-less soccer endpoints for the 2026 FIFA World Cup (league slug fifa.world).
SCOREBOARD_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
)
STANDINGS_URL = (
    "https://site.api.espn.com/apis/v2/sports/soccer/fifa.world/standings"
)
# Core-API per-event endpoint — carries competitions[0].matchNumber (the official "Match 74").
CORE_EVENT_URL = (
    "https://sports.core.api.espn.com/v2/sports/soccer/leagues/fifa.world/events/{id}?lang=en"
)

# The full tournament window (group stage 11 Jun -> final 19 Jul 2026). ESPN's scoreboard
# only returns the current day unless an explicit date range is supplied.
DATE_RANGE = "20260611-20260719"
SCOREBOARD_PARAMS = {"dates": DATE_RANGE, "limit": "400"}

SEASON_YEAR = 2026
COMPETITION_NAME = "2026 FIFA World Cup"

# Poll ESPN every 3 minutes (per requirement). ESPN is unmetered so this is comfortable.
POLL_INTERVAL_SECONDS = 180

HTTP_TIMEOUT_SECONDS = 20

# Group-stage section is opt-in: shown only when FIFA_SHOW_GROUP_STAGE is set truthy (in .env or
# the environment). Absent -> false, so the section is omitted from the bracket payload.
SHOW_GROUP_STAGE = os.getenv("FIFA_SHOW_GROUP_STAGE", "false").lower() in ("1", "true", "yes")

"""FastAPI app: serves the cached tournament snapshot and runs the background poller."""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import config
from .poller import poll_loop, state

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Prime synchronously so the first request has data, then keep polling in the background.
    try:
        await state.refresh_once()
    except Exception as exc:  # don't block startup on a transient ESPN hiccup
        logging.getLogger("fifa2026").warning("initial fetch failed: %s", exc)
    task = asyncio.create_task(poll_loop())
    yield
    task.cancel()


app = FastAPI(title="FIFA 2026 World Cup API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev: the Vite server runs on a different port
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _snapshot_or_503() -> dict:
    if state.snapshot is None:
        raise HTTPException(status_code=503, detail=f"no data yet (last_error={state.last_error})")
    return state.snapshot


@app.get("/api/health")
def health():
    return {
        "ok": state.snapshot is not None,
        "snapshots_generated_at": state.snapshot["generated_at"] if state.snapshot else None,
        "poll_interval_seconds": config.POLL_INTERVAL_SECONDS,
        "last_error": state.last_error,
    }


@app.get("/api/tournament")
def tournament():
    return _snapshot_or_503()


@app.get("/api/bracket")
def bracket():
    return _snapshot_or_503()["bracket"]


@app.get("/api/groups")
def groups():
    return {"groups": _snapshot_or_503()["groups"]}


@app.get("/api/statistics")
def statistics():
    return _snapshot_or_503()["statistics"]


# Also expose the raw written files (so other stacks can grab them over HTTP too).
config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/results_data", StaticFiles(directory=str(config.RESULTS_DIR)), name="results_data")

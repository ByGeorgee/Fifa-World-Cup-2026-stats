"""Thin async client around the ESPN public soccer endpoints.

Returns raw decoded JSON dicts; all normalization happens in bracket.py / groups.py /
statistics.py. Network errors propagate to the caller (the poller), which keeps the last
good state on failure.

The scoreboard does NOT carry the official tournament-wide match number ("Match 74"), but the
core-API per-event endpoint does (``competitions[0].matchNumber``). Match numbers are immutable,
so we fetch them once per event and cache them in memory.
"""
import asyncio
import logging

import httpx

from . import config

log = logging.getLogger("fifa2026.espn")

_HEADERS = {
    # ESPN occasionally 403s requests without a UA.
    "User-Agent": "fifa-2026-bracket/1.0 (+local)",
    "Accept": "application/json",
}

# event id -> official matchNumber (immutable; populated lazily).
_match_number_cache: dict[str, int] = {}

_KNOCKOUT_SLUGS = {
    "round-of-32",
    "round-of-16",
    "quarterfinals",
    "semifinals",
    "3rd-place-match",
    "final",
}


async def _get_json(client: httpx.AsyncClient, url: str, params: dict | None = None) -> dict:
    resp = await client.get(url, params=params)
    resp.raise_for_status()
    return resp.json()


async def _fetch_match_number(client: httpx.AsyncClient, event_id: str) -> None:
    try:
        data = await _get_json(client, config.CORE_EVENT_URL.format(id=event_id))
        mn = (data.get("competitions") or [{}])[0].get("matchNumber")
        if isinstance(mn, int):
            _match_number_cache[event_id] = mn
    except Exception as exc:  # a missing match number just falls back to event-id ordering
        log.warning("matchNumber fetch failed for %s: %s", event_id, exc)


async def fetch_raw() -> tuple[dict, dict, dict]:
    """Fetch scoreboard, standings, and the {event_id: matchNumber} map.

    Returns (scoreboard_json, standings_json, match_numbers).
    """
    async with httpx.AsyncClient(timeout=config.HTTP_TIMEOUT_SECONDS, headers=_HEADERS) as client:
        scoreboard = await _get_json(client, config.SCOREBOARD_URL, config.SCOREBOARD_PARAMS)
        standings = await _get_json(client, config.STANDINGS_URL)

        # Fetch official match numbers only for knockout events we haven't seen yet.
        ko_ids = [
            ev["id"]
            for ev in scoreboard.get("events", [])
            if ev.get("season", {}).get("slug") in _KNOCKOUT_SLUGS and ev.get("id")
        ]
        missing = [i for i in ko_ids if i not in _match_number_cache]
        if missing:
            await asyncio.gather(*(_fetch_match_number(client, i) for i in missing))

    return scoreboard, standings, dict(_match_number_cache)

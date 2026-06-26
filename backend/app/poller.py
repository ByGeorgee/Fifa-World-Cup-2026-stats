"""Background poller: every POLL_INTERVAL fetch ESPN, rebuild the snapshot, write JSON, cache it."""
import asyncio
import logging

from . import config, espn_client, snapshot

log = logging.getLogger("fifa2026.poller")


class TournamentState:
    """Holds the latest good snapshot in memory for the API to serve."""

    def __init__(self) -> None:
        self.snapshot: dict | None = None
        self.last_error: str | None = None

    async def refresh_once(self) -> None:
        scoreboard, standings, match_numbers = await espn_client.fetch_raw()
        snap = snapshot.build_snapshot(scoreboard, standings, match_numbers)
        snapshot.write_snapshot(snap)
        self.snapshot = snap
        self.last_error = None
        log.info(
            "snapshot updated @ %s (%d rounds)",
            snap["generated_at"],
            len(snap["bracket"]["rounds"]),
        )


state = TournamentState()


async def poll_loop() -> None:
    while True:
        try:
            await state.refresh_once()
        except Exception as exc:  # keep last-good state; never kill the loop
            state.last_error = repr(exc)
            log.warning("poll failed, keeping last good state: %s", exc)
        await asyncio.sleep(config.POLL_INTERVAL_SECONDS)

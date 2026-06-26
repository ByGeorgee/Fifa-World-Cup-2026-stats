"""Assemble the combined tournament model and write it to results_data/ as stack-agnostic JSON."""
import json
from datetime import datetime, timezone

from . import bracket as bracket_mod
from . import config
from . import groups as groups_mod
from . import statistics as stats_mod


def build_snapshot(scoreboard: dict, standings: dict, match_numbers: dict | None = None) -> dict:
    """Pure transform: raw ESPN payloads -> the self-describing tournament model."""
    groups = groups_mod.build_groups(standings)
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "espn fifa.world 2026",
        "schema_version": 1,
        "competition": {"name": config.COMPETITION_NAME, "season": config.SEASON_YEAR},
        "bracket": bracket_mod.build_bracket(scoreboard, match_numbers),
        "groups": groups,
        "statistics": stats_mod.build_statistics(scoreboard, groups),
    }


def write_snapshot(snapshot: dict) -> None:
    """Write the combined file plus per-section files into results_data/."""
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    def dump(name: str, obj) -> None:
        path = config.RESULTS_DIR / name
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        tmp.replace(path)  # atomic so readers never see a half-written file

    dump("tournament.json", snapshot)
    dump("bracket.json", {"generated_at": snapshot["generated_at"], **snapshot["bracket"]})
    dump("groups.json", {"generated_at": snapshot["generated_at"], "groups": snapshot["groups"]})
    dump(
        "statistics.json",
        {"generated_at": snapshot["generated_at"], **snapshot["statistics"]},
    )

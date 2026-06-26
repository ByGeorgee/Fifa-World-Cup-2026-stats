"""Normalize ESPN group standings into 12 group tables."""


def _stat(entry: dict, name: str, default=0):
    for s in entry.get("stats", []):
        if s.get("name") == name:
            val = s.get("value")
            return val if val is not None else default
    return default


def _record(entry: dict) -> str:
    for s in entry.get("stats", []):
        if s.get("name") == "overall":
            return s.get("displayValue") or ""
    return ""


def build_groups(standings: dict) -> list[dict]:
    groups = []
    for child in standings.get("children", []):
        entries = child.get("standings", {}).get("entries", [])
        rows = []
        for e in entries:
            team = e.get("team", {}) or {}
            logo = team.get("logo")
            if not logo and team.get("logos"):
                logo = team["logos"][0].get("href")
            rows.append(
                {
                    "rank": int(_stat(e, "rank", 0)),
                    "team": team.get("displayName", "TBD"),
                    "abbreviation": team.get("abbreviation"),
                    "flag_url": logo,
                    "played": int(_stat(e, "gamesPlayed")),
                    "won": int(_stat(e, "wins")),
                    "drawn": int(_stat(e, "ties")),
                    "lost": int(_stat(e, "losses")),
                    "gf": int(_stat(e, "pointsFor")),
                    "ga": int(_stat(e, "pointsAgainst")),
                    "gd": int(_stat(e, "pointDifferential")),
                    "points": int(_stat(e, "points")),
                    "record": _record(e),
                    "advanced": bool(_stat(e, "advanced", 0)),
                }
            )
        rows.sort(key=lambda r: r["rank"] or 99)
        groups.append({"name": child.get("name", "Group"), "standings": rows})
    groups.sort(key=lambda g: g["name"])
    return groups

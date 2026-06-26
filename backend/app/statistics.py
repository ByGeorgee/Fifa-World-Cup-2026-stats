"""Tournament statistics.

Team / tournament aggregates are derived from the (reliable) group standings. Top scorers are a
best-effort aggregation of scoring plays from the scoreboard's per-match ``details`` — ESPN does
not expose a player-leaders feed for fifa.world, so this is sparse until matches are played.
"""


def _build_team_aggregates(groups: list[dict]) -> list[dict]:
    agg = []
    for g in groups:
        for row in g["standings"]:
            agg.append(
                {
                    "team": row["team"],
                    "flag_url": row["flag_url"],
                    "group": g["name"],
                    "played": row["played"],
                    "won": row["won"],
                    "drawn": row["drawn"],
                    "lost": row["lost"],
                    "gf": row["gf"],
                    "ga": row["ga"],
                    "gd": row["gd"],
                    "points": row["points"],
                    "advanced": row["advanced"],
                }
            )
    agg.sort(key=lambda t: (t["points"], t["gd"], t["gf"]), reverse=True)
    return agg


def _tournament_totals(aggregates: list[dict]) -> dict:
    total_goals = sum(t["gf"] for t in aggregates)
    matches_played = sum(t["played"] for t in aggregates) // 2
    best_attack = max(aggregates, key=lambda t: t["gf"], default=None)
    best_defense = min(
        (t for t in aggregates if t["played"] > 0),
        key=lambda t: t["ga"],
        default=None,
    )
    return {
        "matches_played": matches_played,
        "total_goals": total_goals,
        "avg_goals_per_match": round(total_goals / matches_played, 2) if matches_played else 0,
        "teams_advanced": sum(1 for t in aggregates if t["advanced"]),
        "best_attack": {"team": best_attack["team"], "goals": best_attack["gf"]} if best_attack else None,
        "best_defense": {"team": best_defense["team"], "conceded": best_defense["ga"]} if best_defense else None,
    }


def _top_scorers(scoreboard: dict, limit: int = 15) -> list[dict]:
    tally: dict[str, dict] = {}
    for ev in scoreboard.get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        for d in comp.get("details", []) or []:
            if not d.get("scoringPlay"):
                continue
            # Penalty-shootout "goals" shouldn't count as tournament goals.
            type_text = (d.get("type") or {}).get("text", "").lower()
            if "penalty shootout" in type_text or "shootout" in type_text:
                continue
            for ath in d.get("athletesInvolved", []) or []:
                name = ath.get("displayName")
                if not name:
                    continue
                team = ath.get("team", {}) or {}
                rec = tally.setdefault(
                    name, {"player": name, "team": team.get("abbreviation"), "goals": 0}
                )
                rec["goals"] += 1
    scorers = sorted(tally.values(), key=lambda s: s["goals"], reverse=True)
    return scorers[:limit]


def build_statistics(scoreboard: dict, groups: list[dict]) -> dict:
    aggregates = _build_team_aggregates(groups)
    return {
        "tournament_totals": _tournament_totals(aggregates),
        "team_aggregates": aggregates,
        "top_scorers": _top_scorers(scoreboard),
    }

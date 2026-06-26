"""Turn ESPN's flat knockout events into a positioned bracket tree.

Key insight (verified against ESPN's live 2026 data): within a knockout round, ESPN's event
ids are consecutive and ordered by the official match number, and every later-round event names
its feeders by that number (e.g. "Round of 32 3 Winner"). So we can derive the entire bracket
WITHOUT hardcoding FIFA's topology:

  1. group events by round, sort by event id  -> match_number 1..N
  2. parse each slot's placeholder text        -> feeder reference (round, number, winner/loser)
  3. resolve references                         -> feeds_into links + nice "A/B" slot labels
"""
import re

from . import config

# ESPN season slug -> (our round key, display label, short tag, sort order)
ROUND_META = {
    "round-of-32": ("round-of-32", "Round of 32", "R32", 0),
    "round-of-16": ("round-of-16", "Round of 16", "R16", 1),
    "quarterfinals": ("quarterfinals", "Quarter-finals", "QF", 2),
    "semifinals": ("semifinals", "Semi-finals", "SF", 3),
    "final": ("final", "Final", "F", 4),
    "3rd-place-match": ("third-place", "Third-place", "3rd", 5),
}
ID_PREFIX = {
    "round-of-32": "r32",
    "round-of-16": "r16",
    "quarterfinals": "qf",
    "semifinals": "sf",
    "final": "final",
    "third-place": "third",
}

# Feeder references: "<Round> N Winner/Loser" -> which earlier round/match it points at.
_FEEDER_PATTERNS = [
    (re.compile(r"Round of 32 (\d+) Winner"), "round-of-32", "winner"),
    (re.compile(r"Round of 16 (\d+) Winner"), "round-of-16", "winner"),
    (re.compile(r"Quarterfinal (\d+) Winner"), "quarterfinals", "winner"),
    (re.compile(r"Semifinal (\d+) Winner"), "semifinals", "winner"),
    (re.compile(r"Semifinal (\d+) Loser"), "semifinals", "loser"),
]
# Group-slot placeholders -> the image's short code (1F, 2F, 3ABCDF, ...).
_GROUP_WINNER = re.compile(r"Group (\w+) Winner")
_GROUP_SECOND = re.compile(r"Group (\w+) 2nd Place")
_GROUP_THIRD = re.compile(r"Third Place Group ([A-Z/]+)")
# Group-stage events carry their group in altGameNote, e.g. "FIFA World Cup, Group A".
_GROUP_NOTE = re.compile(r"Group ([A-L])")


def _normalize_status(status: dict) -> str:
    """ESPN status.type.state ('pre'/'in'/'post') -> scheduled/live/final."""
    state = (status or {}).get("type", {}).get("state")
    return {"pre": "scheduled", "in": "live", "post": "final"}.get(state, "scheduled")


def _normalize_kickoff(date_str: str) -> str:
    """'2026-06-28T19:00Z' -> '2026-06-28T19:00:00Z' (full ISO-8601 UTC)."""
    if not date_str:
        return date_str
    s = date_str.replace("Z", "+00:00")
    try:
        from datetime import datetime, timezone

        dt = datetime.fromisoformat(s).astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return date_str


def _short_label(display_name: str) -> tuple[str, dict | None]:
    """Return (short_code, feeder_ref_or_None) for a placeholder display name."""
    for pat, rnd, takes in _FEEDER_PATTERNS:
        m = pat.search(display_name)
        if m:
            return display_name, {"round": rnd, "number": int(m.group(1)), "takes": takes}
    m = _GROUP_WINNER.search(display_name)
    if m:
        return "1" + m.group(1), None
    m = _GROUP_SECOND.search(display_name)
    if m:
        return "2" + m.group(1), None
    m = _GROUP_THIRD.search(display_name)
    if m:
        return "3RD " + m.group(1), None  # "Third Place Group B/E/F/I/J" -> "3RD B/E/F/I/J"
    return display_name, None


def _clean_slot(slot: dict) -> dict:
    """Strip the internal 'feeder' key from a slot before emitting it."""
    return {k: v for k, v in slot.items() if k != "feeder"}


def _parse_competitor(comp: dict, state: str) -> dict:
    team = comp.get("team", {}) or {}
    name = team.get("displayName", "TBD")
    logo = team.get("logo") or None
    is_placeholder = logo is None
    short, feeder = _short_label(name) if is_placeholder else (team.get("abbreviation") or name, None)

    score = None
    raw_score = comp.get("score")
    if state in ("live", "final") and raw_score not in (None, ""):
        try:
            score = int(raw_score)
        except (TypeError, ValueError):
            score = None

    return {
        "name": name,
        "short": short,
        "team_id": team.get("id"),
        "abbreviation": team.get("abbreviation"),
        "flag_url": logo,
        "score": score,
        "winner": bool(comp.get("winner")) if state == "final" else False,
        "is_placeholder": is_placeholder,
        "feeder": feeder,  # internal; stripped from final output
    }


def build_bracket(scoreboard: dict, match_numbers: dict | None = None) -> dict:
    """Build the positioned bracket model from an ESPN scoreboard payload.

    ``match_numbers`` maps event id -> official tournament match number (e.g. 74). The within-round
    sequence ("Round of 32 2 Winner") is the rank by match number, so we order each round by it.
    """
    match_numbers = match_numbers or {}
    events = scoreboard.get("events", [])

    # 1. Parse knockout events into raw matches grouped by round.
    by_round: dict[str, list] = {}
    for ev in events:
        slug = ev.get("season", {}).get("slug")
        if slug not in ROUND_META:
            continue
        round_key, _, _, _ = ROUND_META[slug]
        comp = (ev.get("competitions") or [{}])[0]
        state = _normalize_status(comp.get("status") or ev.get("status"))

        home = away = None
        for c in comp.get("competitors", []):
            parsed = _parse_competitor(c, state)
            if c.get("homeAway") == "home":
                home = parsed
            else:
                away = parsed
        if home is None or away is None:  # defensive
            comps = comp.get("competitors", [])
            home = home or (_parse_competitor(comps[0], state) if comps else {})
            away = away or (_parse_competitor(comps[1], state) if len(comps) > 1 else {})

        venue = comp.get("venue", {}) or {}
        match = {
            "round_key": round_key,
            "event_id": ev.get("id"),
            "official_match_number": match_numbers.get(ev.get("id")),
            "kickoff_utc": _normalize_kickoff(ev.get("date", "")),
            "status": state,
            "venue": {
                "name": venue.get("fullName"),
                "city": (venue.get("address") or {}).get("city"),
                "country": (venue.get("address") or {}).get("country"),
            },
            "home": home,
            "away": away,
            "feeds_into": [],
        }
        by_round.setdefault(round_key, []).append(match)

    # 2. Sort each round by official match number (falling back to event id when missing) ->
    #    within-round number; assign stable ids. This is the W-number used in feeder labels.
    index: dict[tuple, dict] = {}
    for round_key, matches in by_round.items():
        matches.sort(
            key=lambda m: (
                m["official_match_number"] if m["official_match_number"] is not None else 10**9,
                int(m["event_id"]) if m["event_id"] else 0,
            )
        )
        prefix = ID_PREFIX[round_key]
        for i, m in enumerate(matches, start=1):
            m["match_number"] = i
            m["id"] = f"{prefix}-{i}" if round_key not in ("final", "third-place") else prefix
            index[(round_key, i)] = m

    # 3. Resolve feeder references -> feeds_into links, then compute each slot's display label.
    for round_key, matches in by_round.items():
        for m in matches:
            for slot_name in ("home", "away"):
                feeder = m[slot_name].get("feeder")
                if not feeder:
                    continue
                src = index.get((feeder["round"], feeder["number"]))
                if not src:
                    continue
                src["feeds_into"].append(
                    {"match_id": m["id"], "slot": slot_name, "takes": feeder["takes"]}
                )
                m[slot_name]["feeder_match_id"] = src["id"]

    # Display label:
    #   - resolved teams         -> the team name
    #   - group-slot placeholder -> short code (1F, 2F, "3RD B/E/F/I/J")
    #   - winner/loser of a match -> abstract feeder tag ("R32 Winner 10", "R16 Winner 5", "SF Loser 1")
    _FEEDER_TAG = {
        "round-of-32": "R32",
        "round-of-16": "R16",
        "quarterfinals": "QF",
        "semifinals": "SF",
    }
    for matches in by_round.values():
        for m in matches:
            for slot_name in ("home", "away"):
                slot = m[slot_name]
                feeder = slot.get("feeder")
                if not slot["is_placeholder"]:
                    slot["display"] = slot["name"]
                elif not feeder:
                    slot["display"] = slot["short"]
                else:
                    tag = _FEEDER_TAG.get(feeder["round"], feeder["round"])
                    slot["display"] = f"{tag} {feeder['takes'].capitalize()} {feeder['number']}"

    # 4. Emit ordered rounds (strip internal 'feeder' keys).
    ordered = sorted(by_round.keys(), key=lambda rk: _round_order(rk))
    rounds = []
    for round_key in ordered:
        _, label, short, _ = _meta_for_key(round_key)
        rounds.append(
            {
                "key": round_key,
                "label": label,
                "short": short,
                "matches": [
                    {
                        "id": m["id"],
                        "match_number": m["match_number"],
                        "official_match_number": m["official_match_number"],
                        "event_id": m["event_id"],
                        "kickoff_utc": m["kickoff_utc"],
                        "status": m["status"],
                        "venue": m["venue"],
                        "home": _clean_slot(m["home"]),
                        "away": _clean_slot(m["away"]),
                        "feeds_into": m["feeds_into"],
                    }
                    for m in by_round[round_key]
                ],
            }
        )
    result = {"rounds": rounds}
    if config.SHOW_GROUP_STAGE:
        result["group_stage"] = build_group_stage(scoreboard)
    return result


def build_group_stage(scoreboard: dict) -> list[dict]:
    """Bucket the 72 group-stage matches by their group (A-L).

    Group-stage events (``season.slug == "group-stage"``) carry resolved teams, scores, venue and
    status just like knockout events, but have no feeder references — advancement is by standings,
    not by match winner — so ``feeds_into`` is always empty and no connectors are drawn.
    """
    by_group: dict[str, list] = {}
    for ev in scoreboard.get("events", []):
        if ev.get("season", {}).get("slug") != "group-stage":
            continue
        comp = (ev.get("competitions") or [{}])[0]
        note = comp.get("altGameNote") or ""
        gm = _GROUP_NOTE.search(note)
        if not gm:  # without a group we can't place the match
            continue
        letter = gm.group(1)

        state = _normalize_status(comp.get("status") or ev.get("status"))
        home = away = None
        for c in comp.get("competitors", []):
            parsed = _parse_competitor(c, state)
            if c.get("homeAway") == "home":
                home = parsed
            else:
                away = parsed
        if home is None or away is None:  # defensive
            comps = comp.get("competitors", [])
            home = home or (_parse_competitor(comps[0], state) if comps else {})
            away = away or (_parse_competitor(comps[1], state) if len(comps) > 1 else {})

        venue = comp.get("venue", {}) or {}
        match = {
            "id": f"g-{ev.get('id')}",
            "event_id": ev.get("id"),
            "kickoff_utc": _normalize_kickoff(ev.get("date", "")),
            "status": state,
            "venue": {
                "name": venue.get("fullName"),
                "city": (venue.get("address") or {}).get("city"),
                "country": (venue.get("address") or {}).get("country"),
            },
            "home": _clean_slot(home),
            "away": _clean_slot(away),
            "feeds_into": [],
        }
        by_group.setdefault(letter, []).append(match)

    groups = []
    for letter in sorted(by_group):
        matches = sorted(by_group[letter], key=lambda m: m["kickoff_utc"] or "")
        groups.append({"group": letter, "label": f"Group {letter}", "matches": matches})
    return groups


def _meta_for_key(round_key: str):
    for meta in ROUND_META.values():
        if meta[0] == round_key:
            return meta
    return (round_key, round_key, round_key, 99)


def _round_order(round_key: str) -> int:
    return _meta_for_key(round_key)[3]

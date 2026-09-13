"""TheSportsDB: team identity search and fixtures, free tier, best-effort."""

from __future__ import annotations

import json

from kit import http

from fandom.models import Match
from fandom.sources.base import SourceError

_API = "https://www.thesportsdb.com/api/v1/json/3"


def _get(path: str) -> dict:
    status, body = http.fetch(f"{_API}{path}")
    if status != 200:
        raise SourceError(path, f"thesportsdb answered HTTP {status}")
    try:
        return json.loads(body)
    except ValueError as error:
        raise SourceError(path, f"thesportsdb answered non-JSON: {str(error)[:80]}") from error


def search_team(name: str) -> list[dict]:
    """Candidate teams for onboarding, already shaped."""
    payload = _get(f"/searchteams.php?t={name.replace(' ', '%20')}")
    return [
        {"id": team.get("idTeam"), "name": team.get("strTeam"),
         "league": team.get("strLeague"), "sport": team.get("strSport")}
        for team in (payload.get("teams") or [])[:5]
    ]


def next_matches(source_id: str, limit: int = 3) -> list[Match]:
    """The team's next fixtures. The free tier often answers empty -- the
    caller treats that as 'fixture not confirmed', never as a fact."""
    payload = _get(f"/eventsnext.php?id={source_id}")
    events = payload.get("events") or []
    return [_match_from(event) for event in events[:limit]]


def last_matches(source_id: str, limit: int = 3) -> list[Match]:
    payload = _get(f"/eventslast.php?id={source_id}")
    events = payload.get("results") or payload.get("events") or []
    return [_match_from(event) for event in events[:limit]]


def _match_from(event: dict) -> Match:
    score = None
    home, away = event.get("intHomeScore"), event.get("intAwayScore")
    if home is not None and away is not None:
        score = f"{home} x {away}"
    # The score existing is not the game ending: a live first half is 0 x 0
    # too. The provider's own status word decides.
    provider_status = str(event.get("strStatus") or "").strip().lower()
    if provider_status in ("match finished", "ft", "aet", "after over time", "finished"):
        status = "finished"
    elif provider_status in ("not started", "ns"):
        status = "scheduled"
    elif provider_status:
        status = "live"
    else:
        status = "finished" if score else "scheduled"
    return Match(
        when=f"{event.get('dateEvent') or ''} {event.get('strTime') or ''}".strip(),
        competition=str(event.get("strLeague") or ""),
        home=str(event.get("strHomeTeam") or ""),
        away=str(event.get("strAwayTeam") or ""),
        status=status,
        score=score,
    )
"""Matchday: fixtures and results, best-effort, honest about what is unknown."""

from __future__ import annotations

from typing import Any

from kit import clock

from fandom.models import Team
from fandom.sources import thesportsdb
from fandom.sources.base import SourceError


def build(team: Team) -> dict[str, Any]:
    """Next fixture and last result for one team, or the honest 'unknown'."""
    if not team.source_id:
        return {
            "team": team.name, "key": team.key,
            "fixture": None, "result": None,
            "note": "sem provedor de jogos para este time -- busque o time para vinculá-lo",
        }
    fixture, fixture_error = _read(lambda: thesportsdb.next_matches(team.source_id))
    result, result_error = _read(lambda: thesportsdb.last_matches(team.source_id))
    return {
        "team": team.name, "key": team.key,
        "fixture": fixture[0].as_dict() if fixture else None,
        "result": result[0].as_dict() if result else None,
        "note": fixture_error or result_error,
    }


def build_all(teams: list[Team]) -> dict[str, Any]:
    """Every followed team's matchday view, for the matchday cron."""
    return {
        "at": clock.iso(),
        "teams": [build(team) for team in teams],
    }


def _read(fetcher) -> tuple[list, str | None]:
    try:
        return fetcher(), None
    except SourceError as error:
        return [], str(error)
    except Exception as error:  # the free tier degrades; nothing here may die
        return [], str(error)[:120]
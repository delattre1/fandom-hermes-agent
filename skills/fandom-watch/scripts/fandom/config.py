"""Agent preferences and the BR-first seed. Missing keys mean onboarding is
unfinished; the seed exists so a fresh agent has something to follow."""

from __future__ import annotations

from typing import Any

from kit.jsonio import load_json, save_json_atomic

REQUIRED_KEYS = ("timezone", "digest_time", "language")

DEFAULTS: dict[str, Any] = {
    "timezone": "UTC",
    "digest_time": "08:30",
    "digest_enabled": True,
    "language": "",                   # "" = mirror the user each turn
    "news_limit_per_team": 5,
    "matchday_times": ["12:00", "19:00"],
}

# Feeds that proved alive on 2026-09-13, per sport. Team-specific feeds are
# mostly dead in Brazil -- the pure alias filter over general feeds is the
# design, and any feed here can die without breaking the digest.
FEEDS = {
    "futebol": [
        "https://ge.globo.com/rss/ge/",
        "https://www.espn.com/espn/rss/soccer/news",
    ],
    "basquete": [
        "https://www.espn.com/espn/rss/nba/news",
        "https://feeds.bbci.co.uk/sport/rss.xml",
    ],
    "futebol_americano": [
        "https://www.espn.com/espn/rss/nfl/news",
        "https://feeds.bbci.co.uk/sport/rss.xml",
    ],
    "esports": [
        "https://feeds.bbci.co.uk/sport/rss.xml",
    ],
}

# The demo seed: Brasileirão, CBLOL, NBA. Onboarding replaces or extends it.
SEED_TEAMS: list[dict[str, Any]] = [
    {
        "key": "brasileirao", "name": "Brasileirão Série A", "sport": "futebol",
        "aliases": ["brasileirão", "brasileirao", "série a", "serie a",
                    "flamengo", "palmeiras", "corinthians", "são paulo", "sao paulo",
                    "grêmio", "gremio", "internacional", "cruzeiro", "atlético-mg",
                    "atletico-mg", "fluminense", "botafogo", "vasco", "santos", "bahia", "fortaleza"],
        "league": "Brasileirão Série A",
    },
    {
        "key": "cblol", "name": "CBLOL", "sport": "esports",
        "aliases": ["cblol", "cboll", "league of legends brasileiro", "lol brasileiro"],
        "league": "CBLOL",
    },
    {
        "key": "nba", "name": "NBA", "sport": "basquete",
        "aliases": ["nba", "basquete", "lakers", "celtics", "warriors", "bucks"],
        "league": "NBA",
    },
]


def config_path(home: str) -> str:
    return f"{home}/config.json"


def load(home: str) -> dict[str, Any]:
    stored = load_json(config_path(home), {}) or {}
    return {**DEFAULTS, **stored}


def save(home: str, config: dict[str, Any]) -> None:
    save_json_atomic(config_path(home), config)


def missing_keys(home: str) -> list[str]:
    """Keys onboarding has not asked about yet -- judged on the FILE, never on
    the defaults: a default is what the agent runs on, not what the user chose."""
    stored = load_json(config_path(home), {}) or {}
    return [key for key in REQUIRED_KEYS if key not in stored]

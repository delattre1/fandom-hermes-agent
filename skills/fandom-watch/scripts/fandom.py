#!/usr/bin/env python3
"""fandom.py -- the Fandom engine's CLI. Every command answers one JSON object.

Commands:
    teams list                                  followed subjects, compact
    teams add <name> --sport S [--aliases ...] [--feed URL]
    teams remove <key>
    search_team <name>                          TheSportsDB candidates
    news [--limit N]                            fetch feeds, filter, cache
    matchday [key ...]                          fixtures and results
    digest                                      the morning payload
    config get | config set KEY=VALUE ...

Exit 0 on success, 2 on failure with an `error` field. stdout is data only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from kit import clock  # noqa: E402

from fandom import config as fandom_config  # noqa: E402
from fandom import store as store_module  # noqa: E402
from fandom.engine import digest, matchday  # noqa: E402
from fandom.models import Sport, Team  # noqa: E402
from fandom.sources import collect_news  # noqa: E402
from fandom.sources import thesportsdb  # noqa: E402
from fandom.store import FandomStore  # noqa: E402

HOME = os.environ.get("FANDOM_HOME", "/var/lib/hermes/fandom")


def emit(payload: object, code: int = 0) -> int:
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return code


def fail(message: str) -> int:
    return emit({"error": message}, 2)


def cmd_teams(args: argparse.Namespace) -> int:
    store = FandomStore(HOME)
    if args.action == "list":
        store.seed_defaults()
        return emit({
            "teams": [store.compact_view(team) for team in store.all()],
            "onboarding_missing": fandom_config.missing_keys(HOME),
        })
    if args.action == "remove":
        try:
            removed = store.remove(args.key)
        except KeyError as error:
            return fail(str(error))
        store.save()
        return emit({"removed": store.compact_view(removed)})

    # add
    name = " ".join(args.name)
    if not name:
        return fail("team name is required")
    try:
        sport = Sport(args.sport)
    except ValueError:
        return fail(f"unknown sport {args.sport!r} -- one of {sorted(s.value for s in Sport)}")
    team = Team(
        key=store_module.team_key_for(name),
        name=name, sport=sport,
        aliases=list(args.aliases),
        feeds=list(args.feed),
        source_id=args.source_id,
    )
    store.add(team)
    store.save()
    return emit({"added": store.compact_view(team)})


def cmd_search_team(args: argparse.Namespace) -> int:
    try:
        candidates = thesportsdb.search_team(" ".join(args.words))
    except Exception as error:
        return fail(f"team search failed: {error}")
    return emit({"query": " ".join(args.words), "results": candidates})


def cmd_news(args: argparse.Namespace) -> int:
    store = FandomStore(HOME)
    store.seed_defaults()  # the BR seed, once, into an empty store
    teams = store.all()
    items, failed = [], []
    for team in teams:
        team_items, team_failed = collect_news(team.feeds, str(team.sport))
        items.extend(team_items)
        failed.extend(team_failed)
    buckets = _filter(items, teams)
    cache = []
    for bucket in buckets.values():
        cache.extend(item.as_dict() for item in bucket)
    store.save_news(cache)
    return emit({
        "at": clock.iso(),
        "teams": {key: [item.as_dict() for item in bucket[:args.limit]]
                  for key, bucket in buckets.items()},
        "failed_sources": failed,
        "sources_read": len(items),
    })


def _filter(items, teams):
    from fandom.engine import news_filter
    return news_filter.filter_news(items, teams)


def cmd_matchday(args: argparse.Namespace) -> int:
    store = FandomStore(HOME)
    teams = [store.get(key) for key in args.keys] if args.keys else store.all()
    return emit(matchday.build_all(teams))


def cmd_digest(args: argparse.Namespace) -> int:
    """Fetch + filter + build in one command -- what the digest cron runs."""
    store = FandomStore(HOME)
    store.seed_defaults()
    teams = store.all()
    items, failed = [], []
    for team in teams:
        team_items, team_failed = collect_news(team.feeds, str(team.sport))
        items.extend(team_items)
        failed.extend(team_failed)
    settings = fandom_config.load(HOME)
    payload = digest.build(teams, items, failed,
                           per_team_limit=int(settings["news_limit_per_team"]))
    payload["timezone"] = settings["timezone"]
    return emit(payload)


def cmd_config(args: argparse.Namespace) -> int:
    if args.action == "get":
        return emit(fandom_config.load(HOME))
    current = fandom_config.load(HOME)
    for pair in args.pairs:
        key, _, raw = pair.partition("=")
        if key not in fandom_config.DEFAULTS:
            return fail(f"unknown config key {key!r}")
        if key == "digest_enabled":
            current[key] = raw.strip().lower() in ("1", "true", "yes", "on")
        else:
            current[key] = raw.strip()
    fandom_config.save(HOME, current)
    return emit({"saved": current, "onboarding_missing": fandom_config.missing_keys(HOME)})


def main() -> int:
    parser = argparse.ArgumentParser(prog="fandom", description=__doc__.splitlines()[0])
    verbs = parser.add_subparsers(dest="command", required=True)

    it = verbs.add_parser("teams")
    sub = it.add_subparsers(dest="action", required=True)
    sub.add_parser("list").set_defaults(run=lambda a: cmd_teams(a), action="list")
    it_add = sub.add_parser("add")
    it_add.add_argument("name", nargs="+")
    it_add.add_argument("--sport", default="futebol")
    it_add.add_argument("--aliases", nargs="*", default=[])
    it_add.add_argument("--feed", action="append", default=[])
    it_add.add_argument("--source-id", default=None)
    it_add.set_defaults(run=lambda a: cmd_teams(a), action="add")
    it_rm = sub.add_parser("remove")
    it_rm.add_argument("key")
    it_rm.set_defaults(run=lambda a: cmd_teams(a), action="remove")

    it = verbs.add_parser("search_team")
    it.add_argument("words", nargs="+")
    it.set_defaults(run=cmd_search_team)

    it = verbs.add_parser("news")
    it.add_argument("--limit", type=int, default=5)
    it.set_defaults(run=cmd_news)

    it = verbs.add_parser("matchday")
    it.add_argument("keys", nargs="*")
    it.set_defaults(run=cmd_matchday)

    verbs.add_parser("digest").set_defaults(run=cmd_digest)

    it = verbs.add_parser("config")
    it.add_argument("action", choices=["get", "set"])
    it.add_argument("pairs", nargs="*")
    it.set_defaults(run=cmd_config)

    args = parser.parse_args()
    try:
        return args.run(args)
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())

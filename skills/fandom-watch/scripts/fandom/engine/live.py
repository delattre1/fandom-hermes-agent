"""Live-game detection from headlines -- pure.

The free fixture providers answer empty, but the news feeds scream: ge
titles literally carry "Flamengo x Corinthians - Ao vivo". A live game is a
headline before it is a score, and the digest may say so -- pointing at the
headline, never at a score nobody confirmed.
"""

from __future__ import annotations

from fandom.engine.news_filter import normalize
from fandom.models import NewsItem

# Strict markers only: "vs" matches previews, and a live headline without
# the word is noise we would rather miss than fake.
_LIVE_MARKERS = ("ao vivo", "live -", " Live".lower().strip())


def is_live_headline(item: NewsItem) -> bool:
    haystack = normalize(item.title)
    if "ao vivo" in haystack:
        return True
    # English newsroom style: "Live - Team v Team" or "Live: ..."
    return haystack.startswith("live ") or " - live" in haystack or " live:" in haystack


def pick_live(items: list[NewsItem]) -> list[NewsItem]:
    """The live-game headlines, deduped by link, newest first."""
    seen: set[str] = set()
    live: list[NewsItem] = []
    for item in sorted(items, key=lambda i: i.published_at, reverse=True):
        if item.link in seen:
            continue
        seen.add(item.link)
        if is_live_headline(item):
            live.append(item)
    return live

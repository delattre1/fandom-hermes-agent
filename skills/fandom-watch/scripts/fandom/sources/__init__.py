"""News sources: RSS feeds, TheSportsDB. One dead source never kills a digest."""

from __future__ import annotations

from collections.abc import Callable

from fandom.sources import gnews, rss, thesportsdb


def feed_sources(team_feeds: list[str], sport: str, *, name: str = "",
                 aliases: list[str] | None = None, language: str = "") -> list[tuple[str, str, Callable[[], list]]]:
    """(url, source_label, reader) tuples for one subject's news sweep.

    Ends with the subject's own Google News query, in the user's language:
    dedicated feeds die or bot-wall, the search feed keeps scenes like CS2
    and every followed team supplied.
    """
    from fandom import config
    urls = list(team_feeds) + list(config.FEEDS.get(sport, []))
    query = gnews.search_url(gnews.terms_for(name, aliases or []), language)
    if query:
        urls.append(query)
    seen: dict[str, tuple[str, str, Callable[[], list]]] = {}
    for url in urls:
        label = url.split("//", 1)[-1].split("/", 1)[0]
        seen.setdefault(url, (url, label, lambda u=url: rss.fetch_feed(u)))
    return list(seen.values())


def collect_news(team_feeds: list[str], sport: str, *, name: str = "",
                 aliases: list[str] | None = None, language: str = "") -> tuple[list, list[str]]:
    """Every item every reachable feed carries, plus the feeds that failed.

    Anything one feed raises degrades to a line in `failed` -- a digest is
    assembled from whatever answered, never aborted.
    """
    items, failed = [], []
    for url, label, reader in feed_sources(
        team_feeds, sport, name=name, aliases=aliases, language=language
    ):
        try:
            items.extend(reader())
        except Exception as error:
            failed.append(f"{label}: {str(error)[:120]}")
    return items, failed


def read_fixture(provider: str, fetcher: Callable[[], object]) -> tuple[object | None, str | None]:
    """A matchday read that degrades instead of dying."""
    try:
        return fetcher(), None
    except Exception as error:  # matchday is best-effort by design
        return None, f"{provider}: {str(error)[:120]}"
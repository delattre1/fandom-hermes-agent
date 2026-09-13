"""The RSS reader against real saved feeds: ge.globo, BBC, malformed bodies."""

import pytest

from fandom.sources import rss
from kit.http import HttpError


class TestRealFeeds:
    def test_ge_globo_parses_all_items(self, ge_feed):
        items = rss.parse(ge_feed, "ge.globo.com")
        assert len(items) >= 80
        assert items[0].title and items[0].link.startswith("http")
        assert items[0].source == "ge.globo.com"

    def test_bbc_parses_all_items(self, bbc_feed):
        items = rss.parse(bbc_feed, "bbc")
        assert len(items) >= 50

    def test_filter_finds_brasileirao_in_real_ge_feed(self, ge_feed):
        from fandom.engine.news_filter import filter_news
        from fandom.models import Sport, Team
        items = rss.parse(ge_feed, "ge")
        seed = Team(key="brasileirao", name="Brasileirão", sport=Sport.FUTEBOL,
                    aliases=["flamengo", "palmeiras", "corinthians", "brasileirão"])
        buckets = filter_news(items, [seed])
        assert len(buckets["brasileirao"]) > 0


class TestEdgeCases:
    def test_malformed_xml_is_a_feed_error(self):
        with pytest.raises(rss.FeedError):
            rss.parse(b"<html>not xml at all", "broken")

    def test_empty_feed_yields_nothing(self):
        assert rss.parse(b"<rss><channel></channel></rss>", "empty") == []

    def test_atom_entries_parse(self):
        atom = (b'<feed xmlns="http://www.w3.org/2005/Atom"><entry>'
                b'<title>PSG x Marseille</title>'
                b'<link href="https://x/atom/1"/><updated>2026-09-13T10:00:00Z</updated>'
                b'</entry></feed>')
        items = rss.parse(atom, "atom.example")
        assert len(items) == 1 and items[0].link == "https://x/atom/1"

    def test_http_error_raises_feed_error(self, monkeypatch):
        monkeypatch.setattr(rss.http, "fetch", lambda url, **kw: (403, b"denied"))
        with pytest.raises(rss.FeedError):
            rss.fetch_feed("https://ge.example/rss")


class TestCollect:
    def test_dead_feed_degrades_never_dies(self, monkeypatch):
        from fandom.sources import collect_news
        def boom(url, **kw):
            raise HttpError("blocked")
        monkeypatch.setattr(rss.http, "fetch", boom)
        items, failed = collect_news([], "futebol")
        assert items == []
        assert len(failed) >= 2  # both futebol feeds reported as degraded
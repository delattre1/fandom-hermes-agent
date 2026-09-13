"""The Google News search feed: URL building, term budget, the CS2 seed."""

import pytest

from fandom.engine.news_filter import filter_news
from fandom.models import NewsItem, Sport, Team
from fandom.sources import gnews


class TestSearchUrl:
    def test_pt_br_locale(self):
        url = gnews.search_url(["CS2", "FURIA"], "pt-BR")
        assert "news.google.com/rss/search?q=" in url
        assert "hl=pt-BR&gl=BR&ceid=BR:pt-419" in url
        assert "when:7d" in url

    def test_en_locale_by_default(self):
        url = gnews.search_url(["NBA"], "")
        assert "hl=en-US&gl=US&ceid=US:en" in url

    def test_terms_capped_at_eight(self):
        url = gnews.search_url([f"term{i}" for i in range(12)], "pt-BR")
        query = url.split("q=")[1].split("&")[0]
        import urllib.parse
        decoded = urllib.parse.unquote_plus(query)
        assert decoded.count("OR") == 7  # 8 terms ride, the ninth waits

    def test_empty_terms_yield_no_url(self):
        assert gnews.search_url(["", " "], "pt-BR") == ""

    def test_name_rides_first(self):
        terms = gnews.terms_for("FURIA", ["furia esports", "pantera", "art", "kscerato"])
        assert terms[0] == "FURIA" and len(terms) <= 8


class TestCs2Seed:
    def test_seed_includes_cs2_scene(self, store):
        store.seed_defaults()
        keys = {t.key for t in store.all()}
        assert "cs2" in keys and "cblol" in keys

    def test_real_cs2_headline_matches_the_scene(self, store):
        store.seed_defaults()
        scene = store.get("cs2")
        headline = NewsItem(
            title="CS2: FURIA atropela PARIVISION no FISSURE Playground 3 - Pichau Arena",
            link="https://news.google.com/x1",
            published_at="2026-09-13T12:00:00+00:00",
            source="news.google.com",
        )
        buckets = filter_news([headline], [scene])
        assert len(buckets["cs2"]) == 1

    def test_unrelated_headline_does_not(self, store):
        store.seed_defaults()
        scene = store.get("cs2")
        buckets = filter_news([news := NewsItem(
            title="Brasileirão: Flamengo vence o clássico",
            link="https://news.google.com/x2",
            published_at="2026-09-13T12:00:00+00:00",
            source="ge",
        )], [scene])
        assert buckets["cs2"] == []
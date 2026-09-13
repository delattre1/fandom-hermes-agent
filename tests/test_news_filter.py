"""The news filter: normalization, aliases, market topics, dedup."""

from kit import clock

from fandom.engine.news_filter import classify, filter_news, normalize, team_matches
from fandom.models import NewsItem, Sport, Team


def team(name="Brasileirão Série A", key="brasileirao", aliases=None) -> Team:
    return Team(key=key, name=name, sport=Sport.FUTEBOL,
                aliases=aliases or ["brasileirão", "flamengo", "mengão", "corinthians", "timão"])


def item(title, link="https://x/1") -> NewsItem:
    return NewsItem(title=title, link=link, published_at="2026-09-13T12:00:00+00:00", source="ge")


class TestNormalize:
    def test_accents_and_case_die(self):
        assert normalize("São Paulo FC") == "sao paulo fc"
        assert normalize("ATLÉTICO-MG") == "atletico mg"
        assert normalize("Timão!") == "timao"

    def test_whitespace_and_punctuation_collapse(self):
        assert normalize("  Flamengo   vence  ") == "flamengo vence"
        assert normalize("Vasco... propõe?") == "vasco propoe"


class TestMatching:
    def test_alias_nickname_matches(self):
        followed = team()
        assert team_matches(item("Timão anuncia renovação"), followed)
        assert team_matches(item("Mengão goleia no Maracanã"), followed)

    def test_unrelated_headline_never_matches(self):
        followed = team()
        assert not team_matches(item("Lakers anunciam renovação"), followed)

    def test_partial_word_does_not_match(self):
        # 'fla' alone is not an alias on purpose: 'flanela' must not match
        followed = team(aliases=["flamengo"])
        assert not team_matches(item("Flanela de força vende no atacado"), followed)


class TestClassify:
    def test_market_headlines(self):
        assert classify(item("Vasco propõe R$ 8 mi por atacante")) == "transfer"
        assert classify(item("Corinthians anuncia reforço de meio-campo")) == "transfer"
        assert classify(item("Palmeiras vence clássico")) == "general"


class TestFilter:
    def test_groups_by_team_newest_first(self):
        followed = team()
        items = [
            NewsItem("Flamengo vence", "https://a/1", "2026-09-12T10:00:00+00:00", "ge"),
            NewsItem("Corinthians empata", "https://b/2", "2026-09-13T09:00:00+00:00", "ge"),
        ]
        buckets = filter_news(items, [followed])
        assert [i.title for i in buckets[followed.key]] == ["Corinthians empata", "Flamengo vence"]

    def test_dedup_by_link_across_feeds(self):
        followed = team()
        items = [
            NewsItem("Flamengo vence", "https://a/1", "2026-09-13T10:00:00+00:00", "ge"),
            NewsItem("Flamengo vence (replica)", "https://a/1", "2026-09-13T11:00:00+00:00", "espn"),
        ]
        buckets = filter_news(items, [followed])
        assert len(buckets[followed.key]) == 1

    def test_same_headline_serves_two_teams(self):
        a = team(key="a", aliases=["flamengo"])
        b = team(key="b", aliases=["nba"])
        items = [NewsItem("Flamengo e NBA no mesmo dia", "https://c/3", "2026-09-13T12:00:00+00:00", "ge")]
        buckets = filter_news(items, [a, b])
        assert len(buckets["a"]) == 1 and len(buckets["b"]) == 1
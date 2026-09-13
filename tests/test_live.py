"""Live detection from real headlines, ge-style and BBC-style."""

from fandom.engine.live import is_live_headline, pick_live
from fandom.models import NewsItem


def item(title, link="https://x/1", at="2026-09-13T20:00:00+00:00") -> NewsItem:
    return NewsItem(title=title, link=link, published_at=at, source="ge")


class TestLiveHeadlines:
    def test_ge_live_style(self):
        assert is_live_headline(item(
            "Flamengo x Corinthians - Campeonato Brasileiro 2026 - Ao vivo - globoesporte.com"))

    def test_accent_free(self):
        assert is_live_headline(item("Fortaleza x Ceará - Ao Vivo - Série B"))

    def test_bbc_live_style(self):
        assert is_live_headline(item("Live - Brazil v Uruguay: World Cup qualifier"))
        assert is_live_headline(item("Live: NBA finals, fourth quarter"))

    def test_preview_and_result_never_match(self):
        assert not is_live_headline(item("Flamengo x Corinthians: veja onde assistir"))
        assert not is_live_headline(item("Corinthians vence o Flamengo por 2 a 1"))
        assert not is_live_headline(item("Stephen Curry impressiona em vídeo"))


class TestPick:
    def test_dedup_and_order(self):
        items = [
            item("Jogo A - Ao vivo", "https://a/1", at="2026-09-13T19:00:00+00:00"),
            item("Jogo A - Ao vivo (replica)", link="https://a/1"),
            item("Notícia comum"),
            item("Jogo B - Ao vivo", "https://b/2", at="2026-09-13T20:30:00+00:00"),
        ]
        live = pick_live(items)
        # dedup keeps the newest copy of a link
        assert [i.title for i in live] == ["Jogo B - Ao vivo", "Jogo A - Ao vivo (replica)"]

    def test_empty_is_empty(self):
        assert pick_live([item("O clássico terminou empatado em 1 a 1")]) == []
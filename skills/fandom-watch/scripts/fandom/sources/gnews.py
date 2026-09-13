"""Google News search feeds: one URL per followed subject.

Dedicated esports and team feeds are mostly dead or bot-walled; Google News'
search RSS is alive, serves any topic, and speaks Portuguese. A follow's
news sweep therefore always includes a query built from its name and
aliases -- that is how a scene like CS2, with no working dedicated feed on
this network, still gets headlines.
"""

from __future__ import annotations

import urllib.parse

_BASE = "https://news.google.com/rss/search"

# Term budget: Google News ignores long OR chains, so the scene name and its
# best aliases ride first and the rest waits for onboarding.
_MAX_TERMS = 8


def search_url(terms: list[str], language: str = "") -> str:
    """The Google News RSS URL for these terms, in the user's language."""
    cleaned = [urllib.parse.quote_plus(term.strip()) for term in terms
               if term and term.strip()][: _MAX_TERMS]
    if not cleaned:
        return ""
    query = "+OR+".join(cleaned) + "+when:7d"
    if language.lower().startswith("pt"):
        locale = "hl=pt-BR&gl=BR&ceid=BR:pt-419"
    else:
        locale = "hl=en-US&gl=US&ceid=US:en"
    return f"https://news.google.com/rss/search?q={query}&{locale}"


def terms_for(team_name: str, aliases: list[str]) -> list[str]:
    """The name rides first; aliases fill the rest of the budget."""
    return [team_name, *aliases][: _MAX_TERMS]
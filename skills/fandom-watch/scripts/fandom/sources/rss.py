"""RSS reader: RSS 2.0 and Atom, namespace-tolerant, via xml.etree."""

from __future__ import annotations

import email.utils
import xml.etree.ElementTree as ET

from kit import clock, http

from fandom.models import NewsItem


class FeedError(RuntimeError):
    """One feed's failure. A digest survives any of these."""


def _local(tag: str) -> str:
    return tag.rpartition("}")[2].lower()


def _find(node: ET.Element, name: str) -> ET.Element | None:
    for child in node.iter():
        if _local(child.tag) == name:
            return child
    return None


def _parse_instant(raw: str | None) -> str:
    if not raw:
        return clock.iso()
    for parser in (email.utils.parsedate_to_datetime,):
        try:
            moment = parser(raw.strip())
            return moment.astimezone(tz=moment.tzinfo).isoformat(timespec="seconds")
        except (ValueError, TypeError):
            continue
    return clock.iso()


def parse(body: bytes, source: str) -> list[NewsItem]:
    """Every item in an RSS or Atom body; raises FeedError when unparseable."""
    try:
        root = ET.fromstring(body)
    except ET.ParseError as error:
        raise FeedError(f"{source}: unparseable XML ({error})") from error

    items: list[NewsItem] = []
    for element in root.iter():
        name = _local(element.tag)
        if name == "item" and element.find(".//title") is not None:
            title = (element.find(".//title").text or "").strip()
            link_node = element.find(".//link")
            link = (link_node.text or "").strip() if link_node is not None else ""
            published = _parse_instant(element.findtext(".//pubDate"))
            if title and link:
                items.append(NewsItem(title=title, link=link,
                                      published_at=published, source=source))
        elif name == "entry":
            title_node = _find(element, "title")
            link_node = _find(element, "link")
            link = (link_node.get("href") or (link_node.text or "")) if link_node is not None else ""
            title = (title_node.text or "").strip() if title_node is not None else ""
            published = _parse_instant(element.findtext("updated") or element.findtext("published"))
            if title and link:
                items.append(NewsItem(title=title, link=link,
                                      published_at=published, source=source))
    return items


def fetch_feed(url: str, *, timeout_s: float = 8.0) -> list[NewsItem]:
    status, body = http.fetch(url, timeout_s=timeout_s)
    if status != 200:
        raise FeedError(f"{url} answered HTTP {status}")
    source = url.split("//", 1)[-1].split("/", 1)[0]
    return parse(body, source)
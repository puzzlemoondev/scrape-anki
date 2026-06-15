from __future__ import annotations

import re
from enum import StrEnum
from html import escape
from typing import Iterator, cast

from bs4 import BeautifulSoup, Tag

from ..model.spec import CardSpec
from ..util.parser import fetch_html_soup


class KoyomiDeck(StrEnum):
    KANSHI = "kanshi"
    WAFU_GETSU_MEI = "wafu_getsu_mei"


_WORD_READING_RE = re.compile(r"^(?P<word>.*?)\s*（(?P<reading>[^）]+)）$")


class KoyomiScraper:
    def __init__(self, url: str, deck: KoyomiDeck):
        self.url = url
        self.deck = deck

    def scrape(self) -> Iterator[CardSpec]:
        soup = fetch_html_soup(self.url)
        if self.deck == KoyomiDeck.KANSHI:
            yield from self._scrape_kanshi(soup)
            return
        if self.deck == KoyomiDeck.WAFU_GETSU_MEI:
            yield from self._scrape_wafu_getsu_mei(soup)
            return

        raise ValueError(f"Unsupported Koyomi deck: {self.deck}")

    def fetch_css(self) -> str:
        return ""

    def _scrape_kanshi(self, soup: BeautifulSoup) -> Iterator[CardSpec]:
        yield from self._scrape_jikkan(soup)
        yield from self._scrape_junishi(soup)
        yield from self._scrape_rokujikkanshi(soup)

    def _scrape_jikkan(self, soup: BeautifulSoup) -> Iterator[CardSpec]:
        table = _find_table(soup, "十干")
        for index, row in enumerate(_data_rows(table), start=1):
            if len(row) < 6:
                raise ValueError(f"Unexpected 十干 row: {row}")

            term, onyomi, gogyou, inyou, gogyou_inyou, kunyomi = row[:6]
            yield CardSpec(
                front=term,
                back=_details_html(
                    [
                        ("分類", "十干"),
                        ("音読み", onyomi),
                        ("訓読み", kunyomi),
                        ("五行", gogyou),
                        ("陰陽", inyou),
                        ("五行陰陽", gogyou_inyou),
                    ]
                ),
                sort=f"001-{index:02d}",
            )

    def _scrape_junishi(self, soup: BeautifulSoup) -> Iterator[CardSpec]:
        table = _find_table(soup, "十二支")
        for index, row in enumerate(_data_rows(table), start=1):
            if len(row) < 4:
                raise ValueError(f"Unexpected 十二支 row: {row}")

            term, onyomi, kunyomi, gogyou = row[:4]
            yield CardSpec(
                front=term,
                back=_details_html(
                    [
                        ("分類", "十二支"),
                        ("音読み", onyomi),
                        ("訓読み", kunyomi),
                        ("五行", gogyou),
                    ]
                ),
                sort=f"002-{index:02d}",
            )

    def _scrape_rokujikkanshi(self, soup: BeautifulSoup) -> Iterator[CardSpec]:
        table = _find_table(soup, "六十干支")
        entries: list[tuple[int, str, str, str]] = []
        for row in _data_rows(table):
            if len(row) < 8:
                raise ValueError(f"Unexpected 六十干支 row: {row}")
            for offset in (0, 4):
                number, term, onyomi, kunyomi = row[offset : offset + 4]
                if not number:
                    continue
                entries.append((int(number), term, onyomi, kunyomi))

        for number, term, onyomi, kunyomi in sorted(entries):
            yield CardSpec(
                front=term,
                back=_details_html(
                    [
                        ("分類", "六十干支"),
                        ("番号", str(number)),
                        ("音読み", onyomi),
                        ("訓読み", kunyomi),
                    ]
                ),
                sort=f"003-{number:02d}",
            )

    def _scrape_wafu_getsu_mei(self, soup: BeautifulSoup) -> Iterator[CardSpec]:
        table = _find_table(soup, "和風月名")
        for index, row in enumerate(_data_rows(table), start=1):
            if len(row) < 3:
                raise ValueError(f"Unexpected 和風月名 row: {row}")

            old_month, word_cell, explanation = row[:3]
            word, reading = _split_word_reading(word_cell)
            yield CardSpec(
                front=word,
                back=_details_html(
                    [
                        ("旧暦の月", old_month),
                        ("読み", reading),
                        ("由来と解説", explanation),
                    ]
                ),
                sort=f"{index:03d}",
            )


def _find_table(soup: BeautifulSoup, caption_text: str) -> Tag:
    for table in soup.find_all("table"):
        if not isinstance(table, Tag):
            continue
        caption = table.find("caption")
        if caption and _cell_text(caption) == caption_text:
            return table
    raise ValueError(f"Could not find table captioned {caption_text}")


def _data_rows(table: Tag) -> Iterator[list[str]]:
    for row in _expanded_rows(table):
        if row and row[0] not in {"十干", "十二支", "番号", "旧暦の月"}:
            yield row


def _expanded_rows(table: Tag) -> list[list[str]]:
    spans: dict[int, tuple[str, int]] = {}
    rows: list[list[str]] = []

    for tr in table.find_all("tr"):
        row: list[str] = []
        col = 0

        def append_spans() -> None:
            nonlocal col
            while col in spans:
                value, remaining = spans[col]
                row.append(value)
                if remaining == 1:
                    del spans[col]
                else:
                    spans[col] = (value, remaining - 1)
                col += 1

        append_spans()
        for cell in tr.find_all(["th", "td"], recursive=False):
            append_spans()
            text = _cell_text(cell)
            rowspan = _span(cell, "rowspan")
            colspan = _span(cell, "colspan")
            for offset in range(colspan):
                row.append(text)
                if rowspan > 1:
                    spans[col + offset] = (text, rowspan - 1)
            col += colspan
        append_spans()
        rows.append(row)

    return rows


def _span(cell: Tag, attr: str) -> int:
    value = cell.get(attr, 1)
    if isinstance(value, list):
        value = value[0] if value else 1
    return int(cast(str | int, value))


def _cell_text(tag: Tag) -> str:
    return " ".join(tag.get_text(" ", strip=True).split())


def _split_word_reading(text: str) -> tuple[str, str]:
    match = _WORD_READING_RE.match(text)
    if not match:
        return text, ""
    return match.group("word").strip(), match.group("reading").strip()


def _details_html(rows: list[tuple[str, str]]) -> str:
    parts = ['<dl class="koyomi-details">']
    for label, value in rows:
        if not value:
            continue
        parts.append(f"<dt>{escape(label)}</dt>")
        parts.append(f"<dd>{escape(value)}</dd>")
    parts.append("</dl>")
    return "".join(parts)

from __future__ import annotations

import json
from dataclasses import dataclass, field
from io import TextIOWrapper
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlparse
from zipfile import ZipFile

import requests

from ..model.spec import CardSpec


PLACES_FULL_URL = (
    "https://raw.githubusercontent.com/mistval/kotoba/master/"
    "resources/quiz_data/places_full.json"
)
MYOUJI_URL = (
    "https://raw.githubusercontent.com/darkgray1981/kanjiquizbot/master/"
    "quizzes/myouji.json"
)


@dataclass(frozen=True)
class OwnerExclusionSources:
    kotoba: list[str] | None = None
    kanjiquizbot: list[str] | None = None
    exclude_kotoba: bool = True
    exclude_kanjiquizbot: bool = True


@dataclass
class _FrequencyEntry:
    word: str
    reading: str
    source_order: int


@dataclass
class _GroupedEntry:
    word: str
    readings: list[str] = field(default_factory=list)
    source_order: int = 0


class TmwFrequencyScraper:
    def __init__(
        self,
        source: Path,
        level: str,
        owner_exclusions: OwnerExclusionSources | None = None,
    ):
        self.source = source
        self.level = level
        self.owner_exclusions = owner_exclusions or OwnerExclusionSources()

    def scrape(self) -> Iterator[CardSpec]:
        exclusion_set = self._build_exclusion_set()
        entries = self._read_entries(exclusion_set)

        grouped_entries: dict[str, _GroupedEntry] = {}
        for entry in entries:
            if entry.word not in grouped_entries:
                grouped_entries[entry.word] = _GroupedEntry(
                    word=entry.word,
                    source_order=entry.source_order,
                )
            grouped_entry = grouped_entries[entry.word]
            if entry.reading not in grouped_entry.readings:
                grouped_entry.readings.append(entry.reading)

        for entry in grouped_entries.values():
            yield CardSpec(
                front=entry.word,
                back=", ".join(entry.readings),
                sort=f"{entry.source_order:010d}",
            )

    def fetch_css(self) -> str:
        return ""

    def _read_entries(
        self,
        exclusion_set: tuple[set[str], set[str]],
    ) -> list[_FrequencyEntry]:
        kanji_exclusion, kana_exclusion = exclusion_set
        entries: list[_FrequencyEntry] = []
        source_order = 0
        for rows in self._iter_meta_json_rows():
            for row in rows:
                source_order += 1
                if self._row_level(row) != self.level:
                    continue

                word = row[0]
                reading = row[2]["reading"]
                if word in kanji_exclusion or reading in kana_exclusion:
                    continue

                entries.append(
                    _FrequencyEntry(
                        word=word,
                        reading=reading,
                        source_order=source_order,
                    )
                )
        return entries

    def _iter_meta_json_rows(self) -> Iterator[list[Any]]:
        source = self.source.resolve(strict=True)
        if source.is_dir():
            for file in sorted(source.glob("term_meta_bank_*.json"), key=_meta_bank_id):
                with file.open("r", encoding="utf-8") as f:
                    yield json.load(f)
            return

        if source.is_file() and source.suffix == ".zip":
            with ZipFile(source) as zip_file:
                names = [
                    name
                    for name in zip_file.namelist()
                    if Path(name).name.startswith("term_meta_bank_")
                    and Path(name).suffix == ".json"
                ]
                for name in sorted(names, key=lambda name: _meta_bank_id(Path(name))):
                    with zip_file.open(name) as f:
                        with TextIOWrapper(f, encoding="utf-8") as text:
                            yield json.load(text)
            return

        raise ValueError(f"TMW source must be a directory or .zip file: {source}")

    def _build_exclusion_set(self) -> tuple[set[str], set[str]]:
        kanji_exclusion: set[str] = set()
        kana_exclusion: set[str] = set()
        if self.owner_exclusions.exclude_kotoba:
            for source in self.owner_exclusions.kotoba or []:
                data = _read_json_source(source)
                cards = data["cards"]
                for card in cards:
                    if not card:
                        continue
                    kanji_exclusion.add(card["question"])
                    kana_exclusion.update(card["answer"])

        if self.owner_exclusions.exclude_kanjiquizbot:
            for source in self.owner_exclusions.kanjiquizbot or []:
                data = _read_json_source(source)
                cards = data["deck"]
                for card in cards:
                    if not card:
                        continue
                    kanji_exclusion.add(card["question"])
                    kana_exclusion.update(card["answers"])

        return kanji_exclusion, kana_exclusion

    def _row_level(self, row: list[Any]) -> str:
        return row[2]["frequency"]["displayValue"]


def _read_json_source(source: str) -> Any:
    if _is_url(source):
        response = requests.get(source)
        response.raise_for_status()
        return response.json()

    with Path(source).open("r", encoding="utf-8") as f:
        return json.load(f)


def _meta_bank_id(path: Path) -> int:
    return int(path.stem.rsplit("_", 1)[1])


def _is_url(source: str) -> bool:
    return urlparse(source).scheme in {"http", "https"}

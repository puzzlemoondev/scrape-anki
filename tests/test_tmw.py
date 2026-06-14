import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from zipfile import ZipFile

from scrape_anki.__main__ import generate_deck
from scrape_anki.config.tmw import (
    TMW_BACK_TEMPLATE,
    TMW_CSS,
    TMW_FRONT_TEMPLATE,
    TmwLevel,
    create_owner_config,
    create_tmw_config,
)
from scrape_anki.scrapers.tmw import (
    MYOUJI_URL,
    PLACES_FULL_URL,
    OwnerExclusionSources,
    TmwFrequencyScraper,
)


def _row(word: str, reading: str, level: str, frequency: int) -> list:
    return [
        word,
        "freq",
        {
            "reading": reading,
            "frequency": {
                "value": frequency,
                "displayValue": level,
            },
        },
    ]


def _write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


class TmwFrequencyScraperTest(unittest.TestCase):
    def test_scrapes_directory_input_by_level_and_groups_readings(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)
            _write_json(
                source / "term_meta_bank_1.json",
                [
                    _row("後", "あと", "Immortal Idol", 20),
                    _row("前", "まえ", "Immortal Idol", 10),
                    _row("学生", "がくせい", "Student", 1),
                ],
            )
            _write_json(
                source / "term_meta_bank_2.json",
                [
                    _row("前", "さき", "Immortal Idol", 11),
                    _row("前", "まえ", "Immortal Idol", 12),
                ],
            )

            cards = list(TmwFrequencyScraper(source, "Immortal Idol").scrape())

        self.assertEqual(
            [(card.front, card.back) for card in cards],
            [
                ("後", "あと"),
                ("前", "まえ, さき"),
            ],
        )
        self.assertEqual(
            [card.sort for card in cards],
            [
                "0000000001",
                "0000000002",
            ],
        )

    def test_sort_uses_absolute_source_order_not_filtered_rank(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)
            _write_json(
                source / "term_meta_bank_1.json",
                [
                    _row("学生一", "がくせいいち", "Student", 1),
                    _row("学生二", "がくせいに", "Student", 2),
                    _row("不死一", "ふしいち", "Immortal Idol", 99999),
                    _row("不死二", "ふしに", "Immortal Idol", 99999),
                ],
            )

            cards = list(TmwFrequencyScraper(source, "Immortal Idol").scrape())

        self.assertEqual(
            [(card.front, card.sort) for card in cards],
            [
                ("不死一", "0000000003"),
                ("不死二", "0000000004"),
            ],
        )

    def test_scrapes_zip_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / "tmw.zip"
            with ZipFile(zip_path, "w") as zip_file:
                zip_file.writestr(
                    "index.json",
                    "{}",
                )
                zip_file.writestr(
                    "term_meta_bank_1.json",
                    json.dumps(
                        [
                            _row("私", "わたし", "Student", 2),
                            _row("言う", "いう", "Student", 1),
                        ],
                        ensure_ascii=False,
                    ),
                )

            cards = list(TmwFrequencyScraper(zip_path, "Student").scrape())

        self.assertEqual(
            [(card.front, card.back) for card in cards],
            [
                ("私", "わたし"),
                ("言う", "いう"),
            ],
        )
        self.assertEqual(
            [card.sort for card in cards],
            [
                "0000000001",
                "0000000002",
            ],
        )

    def test_source_order_wins_when_frequency_values_match_or_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)
            _write_json(
                source / "term_meta_bank_1.json",
                [
                    _row("同値一", "どうちいち", "Owner", 99999),
                    _row("低値後", "ていちあと", "Owner", 1),
                    _row("同値二", "どうちに", "Owner", 99999),
                ],
            )

            cards = list(
                TmwFrequencyScraper(
                    source,
                    "Owner",
                    OwnerExclusionSources(
                        exclude_kotoba=False,
                        exclude_kanjiquizbot=False,
                    ),
                ).scrape()
            )

        self.assertEqual(
            [(card.front, card.sort) for card in cards],
            [
                ("同値一", "0000000001"),
                ("低値後", "0000000002"),
                ("同値二", "0000000003"),
            ],
        )

    def test_meta_banks_are_read_in_numeric_order_for_directory_and_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            source.mkdir()
            _write_json(
                source / "term_meta_bank_10.json",
                [_row("十", "じゅう", "Student", 1)],
            )
            _write_json(
                source / "term_meta_bank_2.json",
                [_row("二", "に", "Student", 1)],
            )
            _write_json(
                source / "term_meta_bank_1.json",
                [_row("一", "いち", "Student", 1)],
            )

            directory_cards = list(TmwFrequencyScraper(source, "Student").scrape())

            zip_path = base / "tmw.zip"
            with ZipFile(zip_path, "w") as zip_file:
                zip_file.writestr(
                    "term_meta_bank_10.json",
                    json.dumps([_row("十", "じゅう", "Student", 1)], ensure_ascii=False),
                )
                zip_file.writestr(
                    "term_meta_bank_2.json",
                    json.dumps([_row("二", "に", "Student", 1)], ensure_ascii=False),
                )
                zip_file.writestr(
                    "term_meta_bank_1.json",
                    json.dumps([_row("一", "いち", "Student", 1)], ensure_ascii=False),
                )
            zip_cards = list(TmwFrequencyScraper(zip_path, "Student").scrape())

        expected = [
            ("一", "0000000001"),
            ("二", "0000000002"),
            ("十", "0000000003"),
        ]
        self.assertEqual([(card.front, card.sort) for card in directory_cards], expected)
        self.assertEqual([(card.front, card.sort) for card in zip_cards], expected)

    def test_owner_exclusions_from_local_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            source.mkdir()
            places_full = base / "places_full.json"
            myouji = base / "myouji.json"

            _write_json(
                source / "term_meta_bank_1.json",
                [
                    _row("東京", "とうきょう", "Owner", 1),
                    _row("山", "とうきょう", "Owner", 2),
                    _row("佐藤", "さとう", "Owner", 3),
                    _row("残る", "のこる", "Owner", 4),
                ],
            )
            _write_json(
                places_full,
                {
                    "cards": [
                        {
                            "question": "東京",
                            "answer": ["とうきょう"],
                        }
                    ]
                },
            )
            _write_json(
                myouji,
                {
                    "deck": [
                        {
                            "question": "佐藤",
                            "answers": ["さとう"],
                        }
                    ]
                },
            )

            cards = list(
                TmwFrequencyScraper(
                    source,
                    "Owner",
                    OwnerExclusionSources(
                        kotoba=[str(places_full)],
                        kanjiquizbot=[str(myouji)],
                    ),
                ).scrape()
            )

        self.assertEqual(
            [(card.front, card.back) for card in cards],
            [("残る", "のこる")],
        )
        self.assertEqual([card.sort for card in cards], ["0000000004"])

    def test_owner_exclusions_can_be_disabled_granularly(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            source.mkdir()
            places_full = base / "places_full.json"
            myouji = base / "myouji.json"

            _write_json(
                source / "term_meta_bank_1.json",
                [
                    _row("東京", "とうきょう", "Owner", 1),
                    _row("佐藤", "さとう", "Owner", 2),
                    _row("残る", "のこる", "Owner", 3),
                ],
            )
            _write_json(
                places_full,
                {"cards": [{"question": "東京", "answer": ["とうきょう"]}]},
            )
            _write_json(
                myouji,
                {"deck": [{"question": "佐藤", "answers": ["さとう"]}]},
            )

            without_places = list(
                TmwFrequencyScraper(
                    source,
                    "Owner",
                    OwnerExclusionSources(
                        kotoba=[str(places_full)],
                        kanjiquizbot=[str(myouji)],
                        exclude_kotoba=False,
                    ),
                ).scrape()
            )
            without_myouji = list(
                TmwFrequencyScraper(
                    source,
                    "Owner",
                    OwnerExclusionSources(
                        kotoba=[str(places_full)],
                        kanjiquizbot=[str(myouji)],
                        exclude_kanjiquizbot=False,
                    ),
                ).scrape()
            )
            without_both = list(
                TmwFrequencyScraper(
                    source,
                    "Owner",
                    OwnerExclusionSources(
                        kotoba=[str(places_full)],
                        kanjiquizbot=[str(myouji)],
                        exclude_kotoba=False,
                        exclude_kanjiquizbot=False,
                    ),
                ).scrape()
            )

        self.assertEqual(
            [(card.front, card.back) for card in without_places],
            [("東京", "とうきょう"), ("残る", "のこる")],
        )
        self.assertEqual(
            [(card.front, card.back) for card in without_myouji],
            [("佐藤", "さとう"), ("残る", "のこる")],
        )
        self.assertEqual(
            [(card.front, card.back) for card in without_both],
            [
                ("東京", "とうきょう"),
                ("佐藤", "さとう"),
                ("残る", "のこる"),
            ],
        )

    def test_owner_exclusions_fetch_missing_json_from_github(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)
            _write_json(
                source / "term_meta_bank_1.json",
                [
                    _row("東京", "とうきょう", "Owner", 1),
                    _row("佐藤", "さとう", "Owner", 2),
                    _row("残る", "のこる", "Owner", 3),
                ],
            )

            def fake_get(url: str) -> Mock:
                response = Mock()
                response.raise_for_status = Mock()
                if url == PLACES_FULL_URL:
                    response.json.return_value = {
                        "cards": [{"question": "東京", "answer": ["とうきょう"]}]
                    }
                elif url == MYOUJI_URL:
                    response.json.return_value = {
                        "deck": [{"question": "佐藤", "answers": ["さとう"]}]
                    }
                else:
                    self.fail(f"unexpected URL: {url}")
                return response

            with patch("scrape_anki.scrapers.tmw.requests.get", side_effect=fake_get):
                cards = list(create_owner_config(source).create_scraper().scrape())

        self.assertEqual(
            [(card.front, card.back) for card in cards],
            [("残る", "のこる")],
        )

    def test_owner_exclusion_url_overrides_replace_default_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)
            _write_json(
                source / "term_meta_bank_1.json",
                [
                    _row("東京", "とうきょう", "Owner", 1),
                    _row("大阪", "おおさか", "Owner", 2),
                    _row("佐藤", "さとう", "Owner", 3),
                    _row("鈴木", "すずき", "Owner", 4),
                    _row("残る", "のこる", "Owner", 5),
                ],
            )

            def fake_get(url: str) -> Mock:
                response = Mock()
                response.raise_for_status = Mock()
                if url == "https://example.test/kotoba.json":
                    response.json.return_value = {
                        "cards": [{"question": "大阪", "answer": ["おおさか"]}]
                    }
                elif url == "https://example.test/kanjiquizbot.json":
                    response.json.return_value = {
                        "deck": [{"question": "鈴木", "answers": ["すずき"]}]
                    }
                else:
                    self.fail(f"default source should not be fetched: {url}")
                return response

            with patch("scrape_anki.scrapers.tmw.requests.get", side_effect=fake_get):
                cards = list(
                    create_owner_config(
                        source,
                        kotoba=["https://example.test/kotoba.json"],
                        kanjiquizbot=["https://example.test/kanjiquizbot.json"],
                    )
                    .create_scraper()
                    .scrape()
                )

        self.assertEqual(
            [(card.front, card.back) for card in cards],
            [
                ("東京", "とうきょう"),
                ("佐藤", "さとう"),
                ("残る", "のこる"),
            ],
        )

    def test_owner_exclusion_family_can_mix_local_paths_and_urls(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            source.mkdir()
            kotoba = base / "kotoba.json"
            _write_json(
                source / "term_meta_bank_1.json",
                [
                    _row("東京", "とうきょう", "Owner", 1),
                    _row("大阪", "おおさか", "Owner", 2),
                    _row("残る", "のこる", "Owner", 3),
                ],
            )
            _write_json(
                kotoba,
                {"cards": [{"question": "東京", "answer": ["とうきょう"]}]},
            )

            def fake_get(url: str) -> Mock:
                response = Mock()
                response.raise_for_status = Mock()
                if url == "https://example.test/kotoba-extra.json":
                    response.json.return_value = {
                        "cards": [{"question": "大阪", "answer": ["おおさか"]}]
                    }
                else:
                    self.fail(f"unexpected URL: {url}")
                return response

            with patch("scrape_anki.scrapers.tmw.requests.get", side_effect=fake_get):
                cards = list(
                    TmwFrequencyScraper(
                        source,
                        "Owner",
                        OwnerExclusionSources(
                            kotoba=[str(kotoba), "https://example.test/kotoba-extra.json"],
                            exclude_kanjiquizbot=False,
                        ),
                    ).scrape()
                )

        self.assertEqual(
            [(card.front, card.back) for card in cards],
            [("残る", "のこる")],
        )

    def test_non_owner_config_has_no_default_exclusion_sources(self):
        config = create_tmw_config(TmwLevel.TRAINEE, Path("source"))
        scraper = config.create_scraper()

        self.assertEqual(scraper.owner_exclusions.kotoba, [])
        self.assertEqual(scraper.owner_exclusions.kanjiquizbot, [])
        self.assertFalse(scraper.owner_exclusions.exclude_kotoba)
        self.assertFalse(scraper.owner_exclusions.exclude_kanjiquizbot)

    def test_non_owner_exclusions_apply_when_sources_are_provided(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            source.mkdir()
            kotoba = base / "kotoba.json"
            _write_json(
                source / "term_meta_bank_1.json",
                [
                    _row("東京", "とうきょう", "Trainee", 1),
                    _row("残る", "のこる", "Trainee", 2),
                ],
            )
            _write_json(
                kotoba,
                {"cards": [{"question": "東京", "answer": ["とうきょう"]}]},
            )

            with patch("scrape_anki.scrapers.tmw.requests.get") as get:
                cards = list(
                    create_tmw_config(
                        TmwLevel.TRAINEE,
                        source,
                        kotoba=[str(kotoba)],
                    )
                    .create_scraper()
                    .scrape()
                )

        get.assert_not_called()
        self.assertEqual(
            [(card.front, card.back, card.sort) for card in cards],
            [("残る", "のこる", "0000000002")],
        )

    def test_tmw_model_uses_requested_card_format(self):
        config = create_owner_config(Path("source"))
        self.assertEqual(
            config.model.fields,
            [
                {"name": "Word"},
                {"name": "Reading"},
                {"name": "Sort"},
            ],
        )
        self.assertEqual(config.model.templates[0]["qfmt"], TMW_FRONT_TEMPLATE)
        self.assertEqual(config.model.templates[0]["afmt"], TMW_BACK_TEMPLATE)
        self.assertEqual(config.model.css, TMW_CSS)
        self.assertNotIn("@font-face", config.model.css)
        self.assertNotIn("Anacreontic", config.model.css)
        self.assertIn('"Hiragino Mincho ProN"', config.model.css)
        self.assertIn("serif", config.model.css)
        self.assertEqual(config.model.model_id, 1424401594)
        self.assertEqual(config.deck.deck_id, 583957534)
        self.assertEqual(config.model.sort_field_index, 2)

    def test_generated_apkg_uses_source_order_sort_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            source.mkdir()
            output = base / "tmw-student.apkg"
            collection = base / "collection.anki2"
            _write_json(
                source / "term_meta_bank_1.json",
                [
                    _row("後", "あと", "Student", 20),
                    _row("前", "まえ", "Student", 10),
                ],
            )

            generate_deck(
                create_tmw_config(TmwLevel.STUDENT, source),
                output,
            )
            with ZipFile(output) as package:
                package.extract("collection.anki2", base)

            with sqlite3.connect(collection) as conn:
                rows = conn.execute(
                    "select flds, sfld from notes order by sfld"
                ).fetchall()

        self.assertEqual(
            rows,
            [
                ("後\x1fあと\x1f0000000001", 1),
                ("前\x1fまえ\x1f0000000002", 2),
            ],
        )

    def test_non_owner_levels_ignore_owner_exclusions(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)
            _write_json(
                source / "term_meta_bank_1.json",
                [_row("東京", "とうきょう", TmwLevel.STUDENT.value, 1)],
            )

            with patch("scrape_anki.scrapers.tmw.requests.get") as get:
                cards = list(TmwFrequencyScraper(source, "Student").scrape())

        get.assert_not_called()
        self.assertEqual(
            [(card.front, card.back) for card in cards],
            [("東京", "とうきょう")],
        )


if __name__ == "__main__":
    unittest.main()

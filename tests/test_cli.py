import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch

from scrape_anki.__main__ import main
from scrape_anki.config.imidas import FOUR_CHARS_CONFIG
from scrape_anki.config.koyomi import KANSHI_CONFIG, WAFU_GETSU_MEI_CONFIG


class CliTest(unittest.TestCase):
    def test_no_args_prints_help(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main([])

        self.assertEqual(code, 0)
        self.assertIn("imidas", stdout.getvalue())
        self.assertIn("koyomi", stdout.getvalue())
        self.assertIn("tmw", stdout.getvalue())

    def test_imidas_deck_routes_to_generate_deck(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "four.apkg"
            with patch("scrape_anki.__main__.generate_deck") as generate_deck:
                code = main(["imidas", "four-chars", "--output", str(output)])

        self.assertEqual(code, 0)
        generate_deck.assert_called_once()
        config, actual_output = generate_deck.call_args.args
        self.assertIs(config, FOUR_CHARS_CONFIG)
        self.assertEqual(actual_output, output)

    def test_koyomi_kanshi_routes_to_generate_deck(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "kanshi.apkg"
            with patch("scrape_anki.__main__.generate_deck") as generate_deck:
                code = main(["koyomi", "kanshi", "--output", str(output)])

        self.assertEqual(code, 0)
        generate_deck.assert_called_once_with(KANSHI_CONFIG, output)

    def test_koyomi_wafu_getsu_mei_routes_to_generate_deck(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "wafu_getsu_mei.apkg"
            with patch("scrape_anki.__main__.generate_deck") as generate_deck:
                code = main(
                    ["koyomi", "wafu-getsu-mei", "--output", str(output)]
                )

        self.assertEqual(code, 0)
        generate_deck.assert_called_once_with(WAFU_GETSU_MEI_CONFIG, output)

    def test_koyomi_all_routes_all_decks_to_output_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "decks"
            with patch("scrape_anki.__main__.generate_deck") as generate_deck:
                code = main(["koyomi", "all", "--output-dir", str(output_dir)])

        self.assertEqual(code, 0)
        self.assertEqual(
            generate_deck.call_args_list,
            [
                call(KANSHI_CONFIG, output_dir / "kanshi.apkg"),
                call(WAFU_GETSU_MEI_CONFIG, output_dir / "wafu_getsu_mei.apkg"),
            ],
        )

    def test_tmw_owner_routes_to_generate_deck_with_generic_exclusion_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "tmw"
            output = Path(tmp) / "tmw-owner.apkg"
            kotoba = Path(tmp) / "kotoba.json"
            kanjiquizbot_url = "https://example.test/kanjiquizbot.json"
            with patch("scrape_anki.__main__.generate_deck") as generate_deck:
                code = main(
                    [
                        "tmw",
                        "owner",
                        "--source",
                        str(source),
                        "--output",
                        str(output),
                        "--exclude-kotoba",
                        str(kotoba),
                        "--exclude-kanjiquizbot",
                        kanjiquizbot_url,
                    ]
                )

        self.assertEqual(code, 0)
        generate_deck.assert_called_once()
        config, actual_output = generate_deck.call_args.args
        self.assertEqual(actual_output, output)
        self.assertEqual(config.deck.name, "TMW Frequency - Owner")

        scraper = config.create_scraper()
        self.assertTrue(scraper.owner_exclusions.exclude_kotoba)
        self.assertTrue(scraper.owner_exclusions.exclude_kanjiquizbot)
        self.assertEqual(scraper.owner_exclusions.kotoba, [str(kotoba)])
        self.assertEqual(scraper.owner_exclusions.kanjiquizbot, [kanjiquizbot_url])

    def test_tmw_owner_can_disable_exclusion_families(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "tmw"
            output = Path(tmp) / "tmw-owner.apkg"
            with patch("scrape_anki.__main__.generate_deck") as generate_deck:
                code = main(
                    [
                        "tmw",
                        "owner",
                        "--source",
                        str(source),
                        "--output",
                        str(output),
                        "--no-exclude-kotoba",
                        "--no-exclude-kanjiquizbot",
                    ]
                )

        self.assertEqual(code, 0)
        scraper = generate_deck.call_args.args[0].create_scraper()
        self.assertFalse(scraper.owner_exclusions.exclude_kotoba)
        self.assertFalse(scraper.owner_exclusions.exclude_kanjiquizbot)

    def test_tmw_non_owner_routes_generic_exclusion_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "tmw"
            output = Path(tmp) / "tmw-trainee.apkg"
            kotoba_url = "https://example.test/kotoba.json"
            with patch("scrape_anki.__main__.generate_deck") as generate_deck:
                code = main(
                    [
                        "tmw",
                        "trainee",
                        "--source",
                        str(source),
                        "--output",
                        str(output),
                        "--exclude-kotoba",
                        kotoba_url,
                    ]
                )

        self.assertEqual(code, 0)
        scraper = generate_deck.call_args.args[0].create_scraper()
        self.assertEqual(scraper.owner_exclusions.kotoba, [kotoba_url])
        self.assertEqual(scraper.owner_exclusions.kanjiquizbot, [])
        self.assertTrue(scraper.owner_exclusions.exclude_kotoba)
        self.assertFalse(scraper.owner_exclusions.exclude_kanjiquizbot)

    def test_tmw_owner_rejects_conflicting_kotoba_exclusion_options(self):
        stderr = io.StringIO()
        with self.assertRaises(SystemExit) as ctx:
            with contextlib.redirect_stderr(stderr):
                main(
                    [
                        "tmw",
                        "owner",
                        "--source",
                        "tmw.zip",
                        "--exclude-kotoba",
                        "kotoba.json",
                        "--no-exclude-kotoba",
                    ]
                )

        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("not allowed with argument", stderr.getvalue())

    def test_tmw_owner_rejects_conflicting_kanjiquizbot_exclusion_options(self):
        stderr = io.StringIO()
        with self.assertRaises(SystemExit) as ctx:
            with contextlib.redirect_stderr(stderr):
                main(
                    [
                        "tmw",
                        "owner",
                        "--source",
                        "tmw.zip",
                        "--exclude-kanjiquizbot",
                        "kanjiquizbot.json",
                        "--no-exclude-kanjiquizbot",
                    ]
                )

        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("not allowed with argument", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

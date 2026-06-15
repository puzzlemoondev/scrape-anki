import argparse
from dataclasses import replace
from pathlib import Path
from typing import Sequence

from .config.imidas import FOUR_CHARS_CONFIG, IDIOM_CONFIG, PROVERB_CONFIG
from .config.koyomi import KANSHI_CONFIG, WAFU_GETSU_MEI_CONFIG
from .config.tmw import TMW_LEVELS_BY_SLUG, create_tmw_config
from .deck.builder import DeckBuilder
from .model.config import Config


IMIDAS_DECKS = {
    "four-chars": (FOUR_CHARS_CONFIG, "four_chars.apkg"),
    "idiom": (IDIOM_CONFIG, "idiom.apkg"),
    "proverb": (PROVERB_CONFIG, "proverb.apkg"),
}

KOYOMI_DECKS = {
    "kanshi": (KANSHI_CONFIG, "kanshi.apkg"),
    "wafu-getsu-mei": (WAFU_GETSU_MEI_CONFIG, "wafu_getsu_mei.apkg"),
}


def generate_deck(config: Config, output_path: Path):
    scraper = config.create_scraper()
    cards = scraper.scrape()

    deck = config.deck
    model = config.model
    tags = config.tags
    if config.fetch_css:
        model = replace(model, css=scraper.fetch_css())
    DeckBuilder().init_deck(deck).init_model(model).add_cards(cards, tags).output(
        output_path
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scrape_anki",
        description="Scrape entries and build Anki decks.",
    )
    subparsers = parser.add_subparsers(dest="site")

    imidas_parser = subparsers.add_parser("imidas", help="Generate Imidas decks")
    imidas_subparsers = imidas_parser.add_subparsers(dest="deck")

    imidas_all_parser = imidas_subparsers.add_parser(
        "all",
        help="Generate all Imidas decks",
    )
    imidas_all_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Directory to write Imidas .apkg files into",
    )
    imidas_all_parser.set_defaults(func=_run_imidas_all)

    for deck_slug, (_, default_output) in IMIDAS_DECKS.items():
        deck_parser = imidas_subparsers.add_parser(
            deck_slug,
            help=f"Generate the {deck_slug} Imidas deck",
        )
        deck_parser.add_argument(
            "--output",
            type=Path,
            default=Path(default_output),
            help="Output .apkg path",
        )
        deck_parser.set_defaults(func=_run_imidas_deck, imidas_deck=deck_slug)

    koyomi_parser = subparsers.add_parser("koyomi", help="Generate NDL Koyomi decks")
    koyomi_subparsers = koyomi_parser.add_subparsers(dest="deck")

    koyomi_all_parser = koyomi_subparsers.add_parser(
        "all",
        help="Generate all NDL Koyomi decks",
    )
    koyomi_all_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Directory to write NDL Koyomi .apkg files into",
    )
    koyomi_all_parser.set_defaults(func=_run_koyomi_all)

    for deck_slug, (_, default_output) in KOYOMI_DECKS.items():
        deck_parser = koyomi_subparsers.add_parser(
            deck_slug,
            help=f"Generate the {deck_slug} NDL Koyomi deck",
        )
        deck_parser.add_argument(
            "--output",
            type=Path,
            default=Path(default_output),
            help="Output .apkg path",
        )
        deck_parser.set_defaults(func=_run_koyomi_deck, koyomi_deck=deck_slug)

    tmw_parser = subparsers.add_parser("tmw", help="Generate TMW frequency decks")
    tmw_subparsers = tmw_parser.add_subparsers(dest="level")

    for level_slug, level in TMW_LEVELS_BY_SLUG.items():
        level_parser = tmw_subparsers.add_parser(
            level_slug,
            help=f"Generate the TMW {level.value} deck",
        )
        level_parser.add_argument(
            "--source",
            type=Path,
            required=True,
            help="TMW frequency zip file or extracted directory",
        )
        level_parser.add_argument(
            "--output",
            type=Path,
            default=Path(f"tmw-{level_slug}.apkg"),
            help="Output .apkg path",
        )
        kotoba_group = level_parser.add_mutually_exclusive_group()
        kotoba_group.add_argument(
            "--exclude-kotoba",
            nargs="+",
            help="Kotoba JSON path or URL to exclude entries from",
        )
        kotoba_group.add_argument(
            "--no-exclude-kotoba",
            action="store_true",
            help="Do not exclude Kotoba entries",
        )
        kanjiquizbot_group = level_parser.add_mutually_exclusive_group()
        kanjiquizbot_group.add_argument(
            "--exclude-kanjiquizbot",
            nargs="+",
            help="KanjiQuizBot JSON path or URL to exclude entries from",
        )
        kanjiquizbot_group.add_argument(
            "--no-exclude-kanjiquizbot",
            action="store_true",
            help="Do not exclude KanjiQuizBot entries",
        )
        level_parser.set_defaults(func=_run_tmw_deck, tmw_level=level)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    args.func(args)
    return 0


def _run_imidas_all(args: argparse.Namespace) -> None:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for config, default_output in IMIDAS_DECKS.values():
        generate_deck(config, args.output_dir / default_output)


def _run_imidas_deck(args: argparse.Namespace) -> None:
    config, _ = IMIDAS_DECKS[args.imidas_deck]
    generate_deck(config, args.output)


def _run_koyomi_all(args: argparse.Namespace) -> None:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for config, default_output in KOYOMI_DECKS.values():
        generate_deck(config, args.output_dir / default_output)


def _run_koyomi_deck(args: argparse.Namespace) -> None:
    config, _ = KOYOMI_DECKS[args.koyomi_deck]
    generate_deck(config, args.output)


def _run_tmw_deck(args: argparse.Namespace) -> None:
    level = args.tmw_level
    config = create_tmw_config(
        level,
        source=args.source,
        kotoba=getattr(args, "exclude_kotoba", None),
        kanjiquizbot=getattr(args, "exclude_kanjiquizbot", None),
        exclude_kotoba=False if getattr(args, "no_exclude_kotoba", False) else None,
        exclude_kanjiquizbot=(
            False if getattr(args, "no_exclude_kanjiquizbot", False) else None
        ),
    )
    generate_deck(config, args.output)


if __name__ == "__main__":
    raise SystemExit(main())

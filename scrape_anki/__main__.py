from dataclasses import replace
from pathlib import Path

from .config.imidas import FOUR_CHARS_CONFIG, IDIOM_CONFIG, PROVERB_CONFIG
from .deck.builder import DeckBuilder
from .model.config import Config


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


if __name__ == "__main__":
    generate_deck(FOUR_CHARS_CONFIG, Path("four_chars.apkg"))
    generate_deck(IDIOM_CONFIG, Path("idiom.apkg"))
    generate_deck(PROVERB_CONFIG, Path("proverb.apkg"))

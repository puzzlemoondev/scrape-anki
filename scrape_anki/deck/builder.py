from pathlib import Path
from typing import Iterable, Self

from genanki import Deck, Model, Note, Package

from ..model.spec import CardSpec, DeckSpec, ModelSpec


class DeckBuilder:
    def __init__(self):
        self.deck = None
        self.model = None

    def init_deck(self, deck: DeckSpec) -> Self:
        self.deck = Deck(
            deck_id=deck.deck_id, name=deck.name, description=deck.description
        )
        return self

    def init_model(self, model: ModelSpec) -> Self:
        self.model = Model(
            model_id=model.model_id,
            name=model.name,
            fields=model.fields,
            templates=model.templates,
            css=model.css,
        )
        return self

    def add_cards(self, cards: Iterable[CardSpec]) -> Self:
        if not self.deck:
            raise ValueError("Deck not initialized")
        if not self.model:
            raise ValueError("Model not initialized")

        for card in cards:
            self.deck.add_note(
                Note(
                    model=self.model,
                    fields=[card.front, card.back],
                )
            )
        return self

    def output(self, path: Path) -> Self:
        Package(self.deck).write_to_file(path)
        return self

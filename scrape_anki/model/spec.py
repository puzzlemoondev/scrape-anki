from dataclasses import dataclass


@dataclass
class DeckSpec:
    deck_id: int
    name: str
    description: str


@dataclass
class ModelSpec:
    model_id: int
    name: str
    fields: list[dict[str, str]]
    templates: list[dict[str, str]]
    css: str


@dataclass
class CardSpec:
    front: str
    back: str

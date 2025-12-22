from dataclasses import dataclass
from typing import Callable, Self

from .scraper import IScraper
from .spec import DeckSpec, ModelSpec


@dataclass
class Config:
    url: str
    deck: DeckSpec
    model: ModelSpec
    fetch_css: bool
    scraper_factory: Callable[[Self], IScraper]

    def create_scraper(self) -> IScraper:
        return self.scraper_factory(self)

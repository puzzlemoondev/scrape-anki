from abc import abstractmethod
from typing import Iterator, Protocol

from .spec import CardSpec


class IScraper(Protocol):
    @abstractmethod
    def scrape(self) -> Iterator[CardSpec]: ...

    @abstractmethod
    def fetch_css(self) -> str: ...

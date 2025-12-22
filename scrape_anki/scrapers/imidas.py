from copy import copy
from typing import Iterator, cast
from urllib.parse import urljoin

from ..model.spec import CardSpec
from ..util.parser import fetch_css, fetch_html_soup


class ImidasScraper:
    def __init__(self, dict_url: str):
        self.dict_url = dict_url
        self.soup = fetch_html_soup(dict_url)

    def scrape(self) -> Iterator[CardSpec]:
        for sound_url in self._find_sound_urls():
            for entry_url in self._find_entry_urls(sound_url):
                if entry := self._scrape_entry(entry_url):
                    yield entry

    def fetch_css(self) -> str:
        return fetch_css(self.soup, self.dict_url)

    def _find_sound_urls(self) -> Iterator[str]:
        if sound_table := self.soup.find("div", {"id": "soundTable"}):
            for li in sound_table.find_all("li"):
                if a := li.find("a"):
                    if href := a.get("href"):
                        url = urljoin(self.dict_url, cast(str, href))
                        yield url

    def _find_entry_urls(self, url: str) -> Iterator[str]:
        soup = fetch_html_soup(url)
        if genre := soup.find("div", {"id": "Genre"}):
            # find entry urls
            if list_box := genre.find("div", {"class": "list-box"}):
                for li in list_box.find_all("li"):
                    if a := li.find("a"):
                        if href := a.get("href"):
                            url = urljoin(self.dict_url, cast(str, href))
                            yield url

            # check for next pages
            if article_list := genre.find("div", {"class": "articleList"}):
                for li in article_list.find_all("li"):
                    if a := li.find("a"):
                        if not (
                            (div := a.find("div")) and div.get_text(strip=True) == ">"
                        ):
                            continue
                        if href := a.get("href"):
                            url = urljoin(self.dict_url, cast(str, href))
                            yield from self._find_entry_urls(url)

    def _scrape_entry(self, url: str) -> CardSpec | None:
        soup = fetch_html_soup(url)
        if back := soup.find("div", {"class": "mainLink"}):
            # remove title bar
            if h2 := back.find("h2"):
                h2.decompose()

            # construct full urls
            for a in back.find_all("a"):
                if href := a.get("href"):
                    a["href"] = urljoin(url, cast(str, href))

            # create a copy of back
            front = copy(back)
            # remove unnecessary elements
            if h3 := front.find("h3"):
                for sibling in h3.find_next_siblings():
                    sibling.decompose()

            print("finished scraping entry:", url)
            return CardSpec(front=str(front), back=str(back))

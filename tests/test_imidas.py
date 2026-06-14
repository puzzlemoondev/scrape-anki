import contextlib
import io
import unittest
from unittest.mock import Mock, patch

from bs4 import BeautifulSoup

from scrape_anki.scrapers.imidas import ImidasScraper


DICT_URL = "https://imidas.jp/fourchars.html"


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


class ImidasScraperTest(unittest.TestCase):
    def test_scrape_uses_local_html_fixtures_without_network(self):
        sound_url = "https://imidas.jp/sound/a.html"
        next_url = "https://imidas.jp/sound/page2.html"
        entry_url = "https://imidas.jp/entry1.html"
        next_entry_url = "https://imidas.jp/entry2.html"
        pages = {
            DICT_URL: """
                <html><body>
                <div id="soundTable">
                  <ul>
                    <li><a href="/sound/a.html">あ</a></li>
                  </ul>
                </div>
                </body></html>
            """,
            sound_url: """
                <html><body>
                <div id="Genre">
                  <div class="list-box">
                    <ul>
                      <li><a href="entry1.html">entry 1</a></li>
                    </ul>
                  </div>
                  <div class="articleList">
                    <ul>
                      <li><a href="/sound/skip.html"><div>1</div></a></li>
                      <li><a href="/sound/page2.html"><div>&gt;</div></a></li>
                    </ul>
                  </div>
                </div>
                </body></html>
            """,
            next_url: """
                <html><body>
                <div id="Genre">
                  <div class="list-box">
                    <ul>
                      <li><a href="/entry2.html">entry 2</a></li>
                    </ul>
                  </div>
                </div>
                </body></html>
            """,
            entry_url: """
                <html><body>
                <div class="mainLink">
                  <h2>removed title</h2>
                  <p><a href="/dict/link.html">四字熟語</a></p>
                  <h3>heading kept on front</h3>
                  <p>detail only on back</p>
                  <img src="/img/example.png" />
                </div>
                </body></html>
            """,
            next_entry_url: """
                <html><body>
                <div class="mainLink">
                  <h2>removed title 2</h2>
                  <p>second card</p>
                  <h3>second heading</h3>
                  <p>second detail</p>
                </div>
                </body></html>
            """,
        }

        def fake_fetch(url: str) -> BeautifulSoup:
            if url not in pages:
                self.fail(f"unexpected fetch: {url}")
            return _soup(pages[url])

        with patch(
            "scrape_anki.scrapers.imidas.fetch_html_soup",
            side_effect=fake_fetch,
        ) as fetch_html_soup:
            with contextlib.redirect_stdout(io.StringIO()):
                cards = list(ImidasScraper(DICT_URL).scrape())

        self.assertEqual(fetch_html_soup.call_count, 5)
        self.assertEqual(len(cards), 2)

        first = cards[0]
        self.assertNotIn("removed title", first.front)
        self.assertNotIn("removed title", first.back)
        self.assertIn("heading kept on front", first.front)
        self.assertNotIn("detail only on back", first.front)
        self.assertIn("detail only on back", first.back)
        self.assertIn('href="https://imidas.jp/dict/link.html"', first.front)
        self.assertIn('src="https://imidas.jp/img/example.png"', first.back)

        self.assertIn("second card", cards[1].front)
        self.assertIn("second detail", cards[1].back)

    def test_scrape_skips_entry_pages_without_main_link(self):
        pages = {
            DICT_URL: """
                <html><body>
                <div id="soundTable">
                  <li><a href="/sound/a.html">あ</a></li>
                </div>
                </body></html>
            """,
            "https://imidas.jp/sound/a.html": """
                <html><body>
                <div id="Genre">
                  <div class="list-box">
                    <li><a href="/missing.html">missing</a></li>
                  </div>
                </div>
                </body></html>
            """,
            "https://imidas.jp/missing.html": """
                <html><body><div class="other">No entry body</div></body></html>
            """,
        }

        with patch(
            "scrape_anki.scrapers.imidas.fetch_html_soup",
            side_effect=lambda url: _soup(pages[url]),
        ):
            cards = list(ImidasScraper(DICT_URL).scrape())

        self.assertEqual(cards, [])

    def test_fetch_css_delegates_with_initial_soup_and_dict_url(self):
        fetched_css = Mock(return_value="body { color: red; }")

        with patch(
            "scrape_anki.scrapers.imidas.fetch_html_soup",
            return_value=_soup("<html><body></body></html>"),
        ):
            with patch("scrape_anki.scrapers.imidas.fetch_css", fetched_css):
                scraper = ImidasScraper(DICT_URL)
                css = scraper.fetch_css()

        self.assertEqual(css, "body { color: red; }")
        fetched_css.assert_called_once_with(scraper.soup, DICT_URL)


if __name__ == "__main__":
    unittest.main()

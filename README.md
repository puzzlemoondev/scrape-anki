# scrape_anki

Scrape dictionary entries and build Anki decks as .apkg files.

## Features

- Scrape entries and format front/back HTML for Anki notes.
- Pull linked site CSS and embed it into the Anki model.
- Generate ready-to-import .apkg files with stable deck/model IDs.

### Currently Supported Sites

- Imidas 日本語辞典

## Requirements

- Python 3.13+
- Network access to the target site

## Install

```bash
uv sync
```

## Usage

Generate the default decks:

```bash
uv run -m scrape_anki
```

## Customize

You can:

- Adjust deck/model by modifying an existing Config.
- Toggle CSS fetching with `fetch_css`.

If you add new configs, call `generate_deck(...)` from
`scrape_anki/__main__.py` or write your own script that imports
`generate_deck` and a `Config`.

## Notes

- Scraping may take a while depending on the site and your connection.
- Please respect the target site's terms of service and robots policies.

# scrape_anki

Build Anki `.apkg` decks from scraper-backed sources.

## Features

- Scrape Imidas dictionary entries into front/back Anki cards.
- Scrape NDL Koyomi tables into Japanese calendar reference decks.
- Convert TMW frequency JSON data into Anki decks.
- Read TMW data from either an extracted directory or the original frequency zip.
- Exclude Owner-level TMW place names and surnames by default.
- Generate ready-to-import `.apkg` files with stable deck/model IDs.

## Supported Sources

- Imidas 日本語辞典
  - `four-chars`
  - `idiom`
  - `proverb`
- TMW frequency data
  - `student`
  - `trainee`
  - `debut-idol`
  - `major-idol`
  - `prima-idol`
  - `divine-idol`
  - `eternal-idol`
  - `immortal-idol`
  - `owner`
- NDL 日本の暦
  - `kanshi`
  - `wafu-getsu-mei`

## Requirements

- asdf
- Python 3.14+
- uv 0.11.21+
- Network access for Imidas scraping
- Network access for NDL Koyomi scraping
- Network access for TMW Owner exclusions only when local exclusion JSON files are not provided

This repo uses asdf-managed tooling. With asdf installed and initialized in your
shell, plain `uv` resolves to the pinned version. Current versions are declared
in:

- `.python-version`
- `.tool-versions`
- `pyproject.toml`

## Install

```bash
asdf install
uv sync
```

## Usage

Show available commands:

```bash
uv run python -m scrape_anki --help
```

### Imidas

Generate all Imidas decks:

```bash
uv run python -m scrape_anki imidas all --output-dir .
```

Generate one Imidas deck:

```bash
uv run python -m scrape_anki imidas four-chars --output four_chars.apkg
uv run python -m scrape_anki imidas idiom --output idiom.apkg
uv run python -m scrape_anki imidas proverb --output proverb.apkg
```

### TMW

Generate a TMW frequency deck from the original zip:

```bash
uv run python -m scrape_anki tmw owner \
  --source "/path/to/[Freq] TMW v2.zip" \
  --output tmw-owner.apkg
```

Generate from an extracted directory:

```bash
uv run python -m scrape_anki tmw immortal-idol \
  --source "/path/to/[Freq] TMW v2" \
  --output tmw-immortal-idol.apkg
```

If `--output` is omitted, TMW commands write `tmw-<level>.apkg`.

TMW exclusion flags are available for every level:

```bash
uv run python -m scrape_anki tmw trainee \
  --source "/path/to/[Freq] TMW v2.zip" \
  --exclude-kotoba /path/to/custom_kotoba.json
```

Owner-level TMW decks enable two exclusion sources by default:

- Kotoba `places_full.json` from its GitHub raw URL
- KanjiQuizBot `myouji.json` from its GitHub raw URL

Other levels have no default exclusions. For any level, `--exclude-kotoba` or
`--exclude-kanjiquizbot` overrides that family with one or more local paths or
URLs:

```bash
uv run python -m scrape_anki tmw owner \
  --source "/path/to/[Freq] TMW v2.zip" \
  --exclude-kotoba /path/to/places_full.json \
  --exclude-kanjiquizbot /path/to/myouji.json
```

Disable either exclusion independently:

```bash
uv run python -m scrape_anki tmw owner \
  --source "/path/to/[Freq] TMW v2.zip" \
  --no-exclude-kotoba

uv run python -m scrape_anki tmw owner \
  --source "/path/to/[Freq] TMW v2.zip" \
  --no-exclude-kanjiquizbot
```

### NDL Koyomi

Generate all NDL Koyomi decks:

```bash
uv run python -m scrape_anki koyomi all --output-dir .
```

Generate one NDL Koyomi deck:

```bash
uv run python -m scrape_anki koyomi kanshi --output kanshi.apkg
uv run python -m scrape_anki koyomi wafu-getsu-mei --output wafu_getsu_mei.apkg
```

## Python API

The main program path is still `generate_deck(config, output_path)`.

```python
from pathlib import Path

from scrape_anki.__main__ import generate_deck
from scrape_anki.config.tmw import create_owner_config

config = create_owner_config(
    source=Path("/path/to/[Freq] TMW v2.zip"),
)

generate_deck(config, Path("tmw-owner.apkg"))
```

## Tests

Run the offline test suite:

```bash
uv run python -m unittest discover -v
```

Run a syntax/import compile check:

```bash
uv run python -m compileall scrape_anki tests
```

## Notes

- Imidas scraping may take a while depending on the site and your connection.
- NDL Koyomi decks are generated from the current NDL table markup.
- TMW non-Owner decks are disk-only once the frequency zip or directory exists locally.
- TMW Owner decks use network only for exclusion fallback JSONs.
- Please respect source-site terms of service and robots policies.

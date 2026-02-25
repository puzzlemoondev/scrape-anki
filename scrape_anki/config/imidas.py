from ..model.config import Config
from ..model.spec import DeckSpec, ModelSpec
from ..scrapers.imidas import ImidasScraper


def _create_imidas_model_spec(model_id: int, name: str) -> ModelSpec:
    return ModelSpec(
        model_id=model_id,
        name=name,
        fields=[
            {
                "name": "Question",
            },
            {
                "name": "Answer",
            },
        ],
        templates=[
            {
                "name": "Card",
                "qfmt": "{{Question}}",
                "afmt": "{{Answer}}",
            }
        ],
        css="",
    )


FOUR_CHARS_CONFIG = Config(
    url="https://imidas.jp/fourchars.html",
    deck=DeckSpec(
        deck_id=1760065007,
        name="スピーチに役立つ四字熟語辞典",
        description="約1600項目を収録した集英社刊の『スピーチに役立つ四字熟語辞典』を完全デジタル化。故事来歴を詳述したほか、類語句と対義語句を豊富に掲示。",
    ),
    model=_create_imidas_model_spec(1556473911, "スピーチに役立つ四字熟語辞典Note"),
    scraper_factory=lambda self: ImidasScraper(self.url),
    fetch_css=True,
    tags=["四字熟語"],
)


IDIOM_CONFIG = Config(
    url="https://imidas.jp/idiom.html",
    deck=DeckSpec(
        deck_id=2112657792,
        name="ルーツでなるほど慣用句辞典",
        description="約2300項目を収録した集英社刊の『ルーツでなるほど慣用句辞典』を完全デジタル化。言葉の意味がよくわかる語源を説明したほか、類語と対義語を豊富に掲示。",
    ),
    model=_create_imidas_model_spec(1982922590, "ルーツでなるほど慣用句辞典Note"),
    scraper_factory=lambda self: ImidasScraper(self.url),
    fetch_css=True,
    tags=["慣用句"],
)

PROVERB_CONFIG = Config(
    url="https://imidas.jp/proverb.html",
    deck=DeckSpec(
        deck_id=1311709292,
        name="会話で使えることわざ辞典",
        description="約2500項目を収録した集英社刊の『会話で使えることわざ辞典』を完全デジタル化。すべての語句に会話形式の用例を示したほか、類義語と対義語も掲示。",
    ),
    model=_create_imidas_model_spec(1480528787, "会話で使えることわざ辞典Note"),
    scraper_factory=lambda self: ImidasScraper(self.url),
    fetch_css=True,
    tags=["ことわざ"],
)

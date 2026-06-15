from ..model.config import Config
from ..model.spec import DeckSpec, ModelSpec
from ..scrapers.koyomi import KoyomiDeck, KoyomiScraper


KANSHI_URL = "https://www.ndl.go.jp/koyomi/chapter3/s1.html"
WAFU_GETSU_MEI_URL = "https://www.ndl.go.jp/koyomi/chapter3/s8.html"

KOYOMI_FRONT_TEMPLATE = "{{Term}}"

KOYOMI_BACK_TEMPLATE = """<div class="koyomi-card">
<div class="koyomi-front">{{FrontSide}}</div>
<hr />
{{Answer}}
</div>"""

KOYOMI_CSS = """.card {
  background-color: #fbfaf7;
  color: #1f1d1a;
  font-family: "Hiragino Mincho ProN", "Yu Mincho", "YuMincho", "Noto Serif CJK JP", serif;
  font-size: 22px;
  line-height: 1.6;
  text-align: center;
}

.koyomi-card {
  margin: 0 auto;
  max-width: 32rem;
}

.koyomi-front {
  font-size: 2.4em;
  line-height: 1.2;
}

.koyomi-details {
  display: grid;
  gap: 0.35rem 1rem;
  grid-template-columns: max-content 1fr;
  margin: 1rem auto 0;
  text-align: left;
}

.koyomi-details dt {
  color: #715b25;
  font-weight: 700;
}

.koyomi-details dd {
  margin: 0;
}"""


def _create_koyomi_model_spec(model_id: int, name: str) -> ModelSpec:
    return ModelSpec(
        model_id=model_id,
        name=name,
        fields=[
            {
                "name": "Term",
            },
            {
                "name": "Answer",
            },
            {
                "name": "Sort",
            },
        ],
        templates=[
            {
                "name": "Card",
                "qfmt": KOYOMI_FRONT_TEMPLATE,
                "afmt": KOYOMI_BACK_TEMPLATE,
            }
        ],
        css=KOYOMI_CSS,
        sort_field_index=2,
    )


KANSHI_CONFIG = Config(
    url=KANSHI_URL,
    deck=DeckSpec(
        deck_id=1806500101,
        name="日本の暦 - 干支",
        description=(
            "国立国会図書館『日本の暦』の干支①六十干支を元にしたデッキ。"
            f" Source: {KANSHI_URL}"
        ),
    ),
    model=_create_koyomi_model_spec(1806500102, "日本の暦 - 干支 Note"),
    scraper_factory=lambda self: KoyomiScraper(self.url, KoyomiDeck.KANSHI),
    fetch_css=False,
    tags=["日本の暦", "干支"],
)

WAFU_GETSU_MEI_CONFIG = Config(
    url=WAFU_GETSU_MEI_URL,
    deck=DeckSpec(
        deck_id=1806500201,
        name="日本の暦 - 和風月名",
        description=(
            "国立国会図書館『日本の暦』の和風月名を元にしたデッキ。"
            f" Source: {WAFU_GETSU_MEI_URL}"
        ),
    ),
    model=_create_koyomi_model_spec(1806500202, "日本の暦 - 和風月名 Note"),
    scraper_factory=lambda self: KoyomiScraper(self.url, KoyomiDeck.WAFU_GETSU_MEI),
    fetch_css=False,
    tags=["日本の暦", "和風月名"],
)

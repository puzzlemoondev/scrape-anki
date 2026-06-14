from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from ..model.config import Config
from ..model.spec import DeckSpec, ModelSpec
from ..scrapers.tmw import (
    MYOUJI_URL,
    PLACES_FULL_URL,
    OwnerExclusionSources,
    TmwFrequencyScraper,
)


class TmwLevel(StrEnum):
    STUDENT = "Student"
    TRAINEE = "Trainee"
    DEBUT_IDOL = "Debut Idol"
    MAJOR_IDOL = "Major Idol"
    PRIMA_IDOL = "Prima Idol"
    DIVINE_IDOL = "Divine Idol"
    ETERNAL_IDOL = "Eternal Idol"
    IMMORTAL_IDOL = "Immortal Idol"
    OWNER = "Owner"


TMW_LEVELS_BY_SLUG = {
    "student": TmwLevel.STUDENT,
    "trainee": TmwLevel.TRAINEE,
    "debut-idol": TmwLevel.DEBUT_IDOL,
    "major-idol": TmwLevel.MAJOR_IDOL,
    "prima-idol": TmwLevel.PRIMA_IDOL,
    "divine-idol": TmwLevel.DIVINE_IDOL,
    "eternal-idol": TmwLevel.ETERNAL_IDOL,
    "immortal-idol": TmwLevel.IMMORTAL_IDOL,
    "owner": TmwLevel.OWNER,
}

TMW_LEVEL_SLUGS = {level: slug for slug, level in TMW_LEVELS_BY_SLUG.items()}

_TMW_IDS = {
    TmwLevel.STUDENT: (1126232225, 2020785031),
    TmwLevel.TRAINEE: (21144807, 612459883),
    TmwLevel.DEBUT_IDOL: (936302523, 722527484),
    TmwLevel.MAJOR_IDOL: (1931259656, 1207140772),
    TmwLevel.PRIMA_IDOL: (890020309, 872954101),
    TmwLevel.DIVINE_IDOL: (176325211, 1590143294),
    TmwLevel.ETERNAL_IDOL: (108859672, 2100133208),
    TmwLevel.IMMORTAL_IDOL: (1909494465, 1137120919),
    TmwLevel.OWNER: (583957534, 1424401594),
}

TMW_FRONT_TEMPLATE = "{{Word}}"

TMW_BACK_TEMPLATE = """<div id=container>
<div id=front>{{FrontSide}}</div>
<hr id=answer>
<div id=reading>{{Reading}}</div>
<hr />
</div>"""

TMW_CSS = """#container {
 display: flex;
 flex-flow: row wrap;
 align-items: flex-start;
 justify-content: center;
}

body {
margin: 0px;
 font-family: "Hiragino Mincho ProN", "Yu Mincho", "YuMincho", "Noto Serif CJK JP", serif;
 font-size: 10vh;
 color: white;
 background-color: black;
text-align: center;
}

* {
 flex-basis: 100%;
 margin: 10px;
}"""


def create_tmw_config(
    level: TmwLevel,
    source: Path,
    kotoba: list[str] | None = None,
    kanjiquizbot: list[str] | None = None,
    exclude_kotoba: bool | None = None,
    exclude_kanjiquizbot: bool | None = None,
) -> Config:
    source = Path(source)
    deck_id, model_id = _TMW_IDS[level]
    kotoba_sources = _resolve_exclusion_sources(level, kotoba, PLACES_FULL_URL)
    kanjiquizbot_sources = _resolve_exclusion_sources(
        level,
        kanjiquizbot,
        MYOUJI_URL,
    )

    return Config(
        url=str(source),
        deck=DeckSpec(
            deck_id=deck_id,
            name=f"TMW Frequency - {level.value}",
            description=f"TMW frequency words filtered to {level.value}.",
        ),
        model=_create_tmw_model_spec(model_id, f"TMW Frequency - {level.value} Note"),
        scraper_factory=lambda self: TmwFrequencyScraper(
            source=source,
            level=level.value,
            owner_exclusions=OwnerExclusionSources(
                kotoba=kotoba_sources,
                kanjiquizbot=kanjiquizbot_sources,
                exclude_kotoba=(
                    bool(kotoba_sources)
                    if exclude_kotoba is None
                    else exclude_kotoba
                ),
                exclude_kanjiquizbot=(
                    bool(kanjiquizbot_sources)
                    if exclude_kanjiquizbot is None
                    else exclude_kanjiquizbot
                ),
            ),
        ),
        fetch_css=False,
        tags=["TMW", TMW_LEVEL_SLUGS[level].replace("-", "_")],
    )


def create_student_config(source: Path) -> Config:
    return create_tmw_config(TmwLevel.STUDENT, source)


def create_trainee_config(source: Path) -> Config:
    return create_tmw_config(TmwLevel.TRAINEE, source)


def create_debut_idol_config(source: Path) -> Config:
    return create_tmw_config(TmwLevel.DEBUT_IDOL, source)


def create_major_idol_config(source: Path) -> Config:
    return create_tmw_config(TmwLevel.MAJOR_IDOL, source)


def create_prima_idol_config(source: Path) -> Config:
    return create_tmw_config(TmwLevel.PRIMA_IDOL, source)


def create_divine_idol_config(source: Path) -> Config:
    return create_tmw_config(TmwLevel.DIVINE_IDOL, source)


def create_eternal_idol_config(source: Path) -> Config:
    return create_tmw_config(TmwLevel.ETERNAL_IDOL, source)


def create_immortal_idol_config(source: Path) -> Config:
    return create_tmw_config(TmwLevel.IMMORTAL_IDOL, source)


def create_owner_config(
    source: Path,
    kotoba: list[str] | None = None,
    kanjiquizbot: list[str] | None = None,
    exclude_kotoba: bool | None = None,
    exclude_kanjiquizbot: bool | None = None,
) -> Config:
    return create_tmw_config(
        TmwLevel.OWNER,
        source,
        kotoba=kotoba,
        kanjiquizbot=kanjiquizbot,
        exclude_kotoba=exclude_kotoba,
        exclude_kanjiquizbot=exclude_kanjiquizbot,
    )


def _resolve_exclusion_sources(
    level: TmwLevel,
    sources: list[str] | None,
    owner_default_source: str,
) -> list[str]:
    if sources is not None:
        return sources
    if level == TmwLevel.OWNER:
        return [owner_default_source]
    return []


def _create_tmw_model_spec(model_id: int, name: str) -> ModelSpec:
    return ModelSpec(
        model_id=model_id,
        name=name,
        fields=[
            {
                "name": "Word",
            },
            {
                "name": "Reading",
            },
            {
                "name": "Sort",
            },
        ],
        templates=[
            {
                "name": "Card",
                "qfmt": TMW_FRONT_TEMPLATE,
                "afmt": TMW_BACK_TEMPLATE,
            }
        ],
        css=TMW_CSS,
        sort_field_index=2,
    )

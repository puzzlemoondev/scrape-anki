import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from scrape_anki.config.koyomi import KANSHI_CONFIG, WAFU_GETSU_MEI_CONFIG
from scrape_anki.scrapers.koyomi import KoyomiDeck, KoyomiScraper


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


class KoyomiScraperTest(unittest.TestCase):
    def test_kanshi_scrapes_all_tables_with_separate_reading_sections(self):
        with patch(
            "scrape_anki.scrapers.koyomi.fetch_html_soup",
            return_value=_soup(_kanshi_html()),
        ):
            cards = list(KoyomiScraper("https://example.test/kanshi", KoyomiDeck.KANSHI).scrape())

        self.assertEqual(len(cards), 82)

        self.assertEqual((cards[0].front, cards[0].sort), ("甲", "001-01"))
        self.assertIn("<dt>分類</dt><dd>十干</dd>", cards[0].back)
        self.assertIn("<dt>音読み</dt><dd>こう</dd>", cards[0].back)
        self.assertIn("<dt>訓読み</dt><dd>きのえ</dd>", cards[0].back)
        self.assertIn("<dt>五行陰陽</dt><dd>木の兄</dd>", cards[0].back)

        self.assertEqual((cards[1].front, cards[1].sort), ("乙", "001-02"))
        self.assertIn("<dt>五行</dt><dd>木</dd>", cards[1].back)

        self.assertEqual((cards[10].front, cards[10].sort), ("子", "002-01"))
        self.assertIn("<dt>分類</dt><dd>十二支</dd>", cards[10].back)
        self.assertIn("<dt>音読み</dt><dd>し</dd>", cards[10].back)
        self.assertIn("<dt>訓読み</dt><dd>ね</dd>", cards[10].back)

        cycle_cards = cards[22:]
        self.assertEqual(len(cycle_cards), 60)
        self.assertEqual((cycle_cards[0].front, cycle_cards[0].sort), ("甲子", "003-01"))
        self.assertIn("<dt>番号</dt><dd>1</dd>", cycle_cards[0].back)
        self.assertIn("<dt>音読み</dt><dd>こうし</dd>", cycle_cards[0].back)
        self.assertIn("<dt>訓読み</dt><dd>きのえね</dd>", cycle_cards[0].back)
        self.assertEqual(
            (cycle_cards[30].front, cycle_cards[30].sort),
            ("甲午", "003-31"),
        )

    def test_wafu_getsu_mei_scrapes_months_and_multiline_readings(self):
        with patch(
            "scrape_anki.scrapers.koyomi.fetch_html_soup",
            return_value=_soup(_wafu_getsu_mei_html()),
        ):
            cards = list(
                KoyomiScraper(
                    "https://example.test/wafu-getsu-mei",
                    KoyomiDeck.WAFU_GETSU_MEI,
                ).scrape()
            )

        self.assertEqual(len(cards), 12)
        self.assertEqual((cards[0].front, cards[0].sort), ("睦月", "001"))
        self.assertIn("<dt>旧暦の月</dt><dd>1月</dd>", cards[0].back)
        self.assertIn("<dt>読み</dt><dd>むつき</dd>", cards[0].back)
        self.assertIn("睦び", cards[0].back)

        self.assertEqual((cards[5].front, cards[5].sort), ("水無月", "006"))
        self.assertIn("<dt>読み</dt><dd>みなづき、みなつき</dd>", cards[5].back)
        self.assertIn("田に水を引く月", cards[5].back)

    def test_koyomi_models_include_sort_field(self):
        self.assertEqual(KANSHI_CONFIG.model.sort_field_index, 2)
        self.assertEqual(WAFU_GETSU_MEI_CONFIG.model.sort_field_index, 2)
        self.assertEqual(
            [field["name"] for field in KANSHI_CONFIG.model.fields],
            ["Term", "Answer", "Sort"],
        )


def _kanshi_html() -> str:
    return f"""
    <html><body>
      {_jikkan_table()}
      {_junishi_table()}
      {_rokujikkanshi_table()}
    </body></html>
    """


def _jikkan_table() -> str:
    stems = [
        ("甲", "こう", "木", "陽（兄）", "木の兄", "きのえ"),
        ("乙", "おつ", "木", "陰（弟）", "木の弟", "きのと"),
        ("丙", "へい", "火", "陽（兄）", "火の兄", "ひのえ"),
        ("丁", "てい", "火", "陰（弟）", "火の弟", "ひのと"),
        ("戊", "ぼ", "土", "陽（兄）", "土の兄", "つちのえ"),
        ("己", "き", "土", "陰（弟）", "土の弟", "つちのと"),
        ("庚", "こう", "金", "陽（兄）", "金の兄", "かのえ"),
        ("辛", "しん", "金", "陰（弟）", "金の弟", "かのと"),
        ("壬", "じん", "水", "陽（兄）", "水の兄", "みずのえ"),
        ("癸", "き", "水", "陰（弟）", "水の弟", "みずのと"),
    ]
    rows = [
        """
        <tr>
          <th>十干</th><th>音読み</th><th>五行</th>
          <th>陰陽</th><th>五行陰陽</th><th>訓読み</th>
        </tr>
        """
    ]
    for index in range(0, len(stems), 2):
        first = stems[index]
        second = stems[index + 1]
        rows.append(
            f"""
            <tr>
              <td>{first[0]}</td><td>{first[1]}</td>
              <td rowspan="2">{first[2]}</td>
              <td>{first[3]}</td><td>{first[4]}</td><td>{first[5]}</td>
            </tr>
            <tr>
              <td>{second[0]}</td><td>{second[1]}</td>
              <td>{second[3]}</td><td>{second[4]}</td><td>{second[5]}</td>
            </tr>
            """
        )
    return f"<table><caption><span>十干</span></caption><tbody>{''.join(rows)}</tbody></table>"


def _junishi_table() -> str:
    branches = [
        ("子", "し", "ね", "水"),
        ("丑", "ちゅう", "うし", "土"),
        ("寅", "いん", "とら", "木"),
        ("卯", "ぼう", "う", "木"),
        ("辰", "しん", "たつ", "土"),
        ("巳", "し", "み", "火"),
        ("午", "ご", "うま", "火"),
        ("未", "び", "ひつじ", "土"),
        ("申", "しん", "さる", "金"),
        ("酉", "ゆう", "とり", "金"),
        ("戌", "じゅつ", "いぬ", "土"),
        ("亥", "がい", "い", "水"),
    ]
    rows = [
        "<tr><th>十二支</th><th>音読み</th><th>訓読み</th><th>五行</th></tr>"
    ]
    rows.extend(
        f"<tr><td>{term}</td><td>{onyomi}</td><td>{kunyomi}</td><td>{gogyou}</td></tr>"
        for term, onyomi, kunyomi, gogyou in branches
    )
    return f"<table><caption><span>十二支</span></caption><tbody>{''.join(rows)}</tbody></table>"


def _rokujikkanshi_table() -> str:
    rows = [
        """
        <tr>
          <th>番号</th><th>干支</th><th>音読み</th><th>訓読み</th>
          <th>番号</th><th>干支</th><th>音読み</th><th>訓読み</th>
        </tr>
        """
    ]
    for number in range(1, 31):
        left = _rokujikkanshi_entry(number)
        right = _rokujikkanshi_entry(number + 30)
        rows.append(
            f"""
            <tr>
              <td>{number}</td><td>{left[0]}</td><td>{left[1]}</td><td>{left[2]}</td>
              <td>{number + 30}</td><td>{right[0]}</td><td>{right[1]}</td><td>{right[2]}</td>
            </tr>
            """
        )
    return f"<table><caption><span>六十干支</span></caption><tbody>{''.join(rows)}</tbody></table>"


def _rokujikkanshi_entry(number: int) -> tuple[str, str, str]:
    if number == 1:
        return "甲子", "こうし", "きのえね"
    if number == 31:
        return "甲午", "こうご", "きのえうま"
    return f"干支{number}", f"おん{number}", f"くん{number}"


def _wafu_getsu_mei_html() -> str:
    months = [
        ("1月", "睦月（むつき）", "正月に親類一同が集まる、睦び（親しくする）の月。"),
        ("2月", "如月（きさらぎ）", "衣更着（きさらぎ）とも言う。"),
        ("3月", "弥生（やよい）", "木草弥生い茂る月。"),
        ("4月", "卯月（うづき）", "卯の花の月。"),
        ("5月", "皐月（さつき）", "早苗を植える月。"),
        ("6月", "水無月<br />（みなづき、みなつき）", "田に水を引く月の意と言われる。"),
        ("7月", "文月<br />（ふみづき、ふづき）", "稲の穂が実る月。"),
        ("8月", "葉月<br />（はづき、はつき）", "木々の葉落ち月。"),
        ("9月", "長月<br />（ながつき、ながづき）", "夜長月。"),
        ("10月", "神無月（かんなづき）", "神の月の意味。"),
        ("11月", "霜月（しもつき）", "霜の降る月。"),
        ("12月", "師走（しわす）", "師匠といえども走り回る月。"),
    ]
    rows = [
        "<tr><th>旧暦の月</th><th>和風月名</th><th>由来と解説</th></tr>"
    ]
    rows.extend(
        f"<tr><td>{month}</td><td>{word}</td><td>{explanation}</td></tr>"
        for month, word, explanation in months
    )
    return f"""
    <html><body>
      <table>
        <caption><span>和風月名</span></caption>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </body></html>
    """


if __name__ == "__main__":
    unittest.main()

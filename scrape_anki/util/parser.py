import warnings
from typing import cast
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag, XMLParsedAsHTMLWarning
from bs4.element import AttributeValueList


def extract_attrs(attr: str | AttributeValueList | None) -> list[str]:
    if attr is None:
        return []
    if isinstance(attr, str):
        return [attr]
    return [attr_item for attr_item in attr]


def fetch_html(url: str) -> str:
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def fetch_html_soup(url: str) -> BeautifulSoup:
    response = requests.get(url)
    response.raise_for_status()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
        return BeautifulSoup(response.content, "lxml")


def fetch_css(soup: BeautifulSoup, base_url: str) -> str:
    css_content = ""
    for css in soup.find_all("link"):
        if rels := extract_attrs(css.get("rel")):
            if "stylesheet" not in rels:
                continue

        if types := extract_attrs(css.get("type")):
            if "text/css" not in types:
                continue

        if href := css.get("href"):
            css_href = cast(str, href)
            if not css_href.lower().endswith(".css"):
                continue

            css_url = urljoin(base_url, css_href)
            css_response = requests.get(css_url)
            css_response.raise_for_status()
            css_content += css_response.text

    return css_content


def restore_full_urls(tag: Tag, base_url: str) -> Tag:
    for a in tag.find_all("a"):
        if href := a.get("href"):
            a["href"] = urljoin(base_url, cast(str, href))
    for img in tag.find_all("img"):
        if src := img.get("src"):
            img["src"] = urljoin(base_url, cast(str, src))
    return tag

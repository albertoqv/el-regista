from __future__ import annotations

import re
from datetime import datetime

from bs4 import BeautifulSoup

from player_scouting.domain.market_value import MarketValuePoint

PROFILE_PATH_PATTERN = re.compile(r"^/[^/]+/profil/spieler/\d+$")


def extract_profile_path(search_results_html: str) -> str | None:
    soup = BeautifulSoup(search_results_html, "html.parser")
    for anchor in soup.find_all("a", href=PROFILE_PATH_PATTERN):
        href = anchor.get("href")
        if isinstance(href, str):
            return href
    return None


def extract_preferred_foot(profile_html: str) -> str | None:
    soup = BeautifulSoup(profile_html, "html.parser")
    for label in soup.find_all("span", class_="info-table__content--regular"):
        if label.get_text(strip=True).rstrip(":").lower() != "foot":
            continue
        value = label.find_next_sibling("span", class_="info-table__content--bold")
        if value is not None:
            return value.get_text(strip=True).lower()
    return None


def to_market_value_points(raw_points: list[dict]) -> list[MarketValuePoint]:
    points = [
        MarketValuePoint(
            as_of=datetime.strptime(raw["datum_mw"], "%d/%m/%Y").date(),
            amount_eur=int(raw["y"]),
            club=raw["verein"],
        )
        for raw in raw_points
    ]
    return sorted(points, key=lambda point: point.as_of)

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime

from bs4 import BeautifulSoup

from player_scouting.domain.market_value import MarketValuePoint

PROFILE_PATH_PATTERN = re.compile(r"^/[^/]+/profil/spieler/\d+$")
_BIRTH_DATE_PATTERN = re.compile(r"(\d{2})/(\d{2})/(\d{4})")

# Search result row cells (verified live): name, position, club, age, nation, value.
_CLUB_CELL = 2
_AGE_CELL = 3


@dataclass(frozen=True)
class SearchCandidate:
    profile_path: str
    name: str
    club: str | None
    age: int | None


def extract_search_candidates(search_results_html: str) -> list[SearchCandidate]:
    soup = BeautifulSoup(search_results_html, "html.parser")
    candidates = []
    for table in soup.select("table.items"):
        for row in table.select(":scope > tbody > tr"):
            link = row.find("a", href=PROFILE_PATH_PATTERN)
            if link is None:
                continue
            cells = row.find_all("td", recursive=False)
            club_image = (
                cells[_CLUB_CELL].find("img") if len(cells) > _CLUB_CELL else None
            )
            age_text = (
                cells[_AGE_CELL].get_text(strip=True) if len(cells) > _AGE_CELL else ""
            )
            title = link.get("title")
            candidates.append(
                SearchCandidate(
                    profile_path=str(link["href"]),
                    name=str(title) if title else link.get_text(strip=True),
                    club=str(club_image["title"]) if club_image else None,
                    age=int(age_text) if age_text.isdigit() else None,
                )
            )
    return candidates


def extract_photo_url(profile_html: str) -> str | None:
    soup = BeautifulSoup(profile_html, "html.parser")
    image = soup.find("img", class_="data-header__profile-image")
    source = image.get("src") if image else None
    return str(source) if source else None


def extract_date_of_birth(profile_html: str) -> date | None:
    soup = BeautifulSoup(profile_html, "html.parser")
    item = soup.find(attrs={"itemprop": "birthDate"})
    match = _BIRTH_DATE_PATTERN.search(item.get_text()) if item else None
    if match is None:
        return None
    day, month, year = (int(part) for part in match.groups())
    return date(year, month, day)


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

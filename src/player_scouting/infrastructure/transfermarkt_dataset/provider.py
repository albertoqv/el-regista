from __future__ import annotations

import csv
import io
import zipfile
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

from player_scouting.application.ports import DatasetProfile, DatasetSeasonRow
from player_scouting.domain.market_value import MarketValuePoint
from player_scouting.domain.statistics import Statistics
from player_scouting.infrastructure.transfermarkt_dataset.mapper import (
    OTHER_LEAGUES,
    to_profile,
    to_valuation,
)

# Only players active in the last seasons: the archive also has retired ones.
DEFAULT_ACTIVE_SINCE = 2023


class ArchiveClient(Protocol):
    def download_archive(self) -> Path: ...


class TransfermarktDatasetZipProvider:
    """Reads the public dataset's CSVs straight from the zip, row by row."""

    def __init__(
        self, client: ArchiveClient, active_since: int = DEFAULT_ACTIVE_SINCE
    ) -> None:
        self._client = client
        self._active_since = active_since
        self._path: Path | None = None

    def profiles(self) -> list[DatasetProfile]:
        active = {
            row["player_id"]: row
            for row in self._rows("players.csv")
            if row["last_season"] and int(row["last_season"]) >= self._active_since
        }
        valuations: dict[str, list[MarketValuePoint]] = defaultdict(list)
        for row in self._rows("player_valuations.csv"):
            if row["player_id"] in active:
                point = to_valuation(row)
                if point is not None:
                    valuations[row["player_id"]].append(point)
        profiles = []
        for player_id, row in active.items():
            points = tuple(sorted(valuations[player_id], key=lambda p: p.as_of))
            profile = to_profile(row, points)
            if profile is not None:
                profiles.append(profile)
        return profiles

    def season_rows(self, start_year: int) -> list[DatasetSeasonRow]:
        season = str(start_year)
        games = {
            row["game_id"]
            for row in self._rows("games.csv")
            if row["season"] == season and row["competition_id"] in OTHER_LEAGUES
        }
        clubs = {row["club_id"]: row["name"] for row in self._rows("clubs.csv")}
        totals: dict[tuple[str, str], dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        last_club: dict[tuple[str, str], tuple[str, str]] = {}
        for row in self._rows("appearances.csv"):
            if row["game_id"] not in games:
                continue
            key = (row["player_id"], row["competition_id"])
            for field in (
                "goals",
                "assists",
                "minutes_played",
                "yellow_cards",
                "red_cards",
            ):
                totals[key][field] += int(row[field] or 0)
            # Mid-season move inside the league: keep the latest club.
            if key not in last_club or row["date"] >= last_club[key][0]:
                last_club[key] = (row["date"], row["player_club_id"])
        return [
            DatasetSeasonRow(
                transfermarkt_id=int(player_id),
                competition=OTHER_LEAGUES[competition_id],
                season_label=season,
                team=clubs.get(last_club[(player_id, competition_id)][1]),
                statistics=Statistics(
                    goals=values["goals"],
                    assists=values["assists"],
                    minutes_played=values["minutes_played"],
                    yellow_cards=values["yellow_cards"],
                    red_cards=values["red_cards"],
                ),
            )
            for (player_id, competition_id), values in totals.items()
        ]

    def _rows(self, name: str) -> Iterator[dict[str, str]]:
        if self._path is None:
            self._path = self._client.download_archive()
        with zipfile.ZipFile(self._path) as archive, archive.open(name) as raw:
            yield from csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8"))

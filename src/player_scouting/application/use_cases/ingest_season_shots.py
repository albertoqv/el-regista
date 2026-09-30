from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field

from player_scouting.application.ports import ShotProvider, ShotRepository
from player_scouting.domain.shots import mark_decisive_goals

# One request per match; keep the pace gentle with the source.
PAUSE_BETWEEN_MATCHES_SECONDS = 1.0


@dataclass(frozen=True)
class ShotIngestionSummary:
    matches: int
    shots: int
    remaining: int


@dataclass
class IngestSeasonShotsUseCase:
    provider: ShotProvider
    repository: ShotRepository
    pause: Callable[[float], None] = field(default=time.sleep)

    def execute(self, start_year: int, limit: int) -> ShotIngestionSummary:
        known = self.repository.known_match_ids(str(start_year))
        pending = sorted(
            (
                m
                for m in self.provider.list_played_matches(start_year)
                if m.match_id not in known
            ),
            key=lambda match: (match.played_on, match.match_id),
        )
        batch = pending[:limit]
        shots = 0
        for index, match in enumerate(batch):
            if index:
                self.pause(PAUSE_BETWEEN_MATCHES_SECONDS)
            marked = mark_decisive_goals(self.provider.get_match_shots(match))
            self.repository.save_match(match, marked)
            shots += len(marked)
        return ShotIngestionSummary(
            matches=len(batch), shots=shots, remaining=len(pending) - len(batch)
        )

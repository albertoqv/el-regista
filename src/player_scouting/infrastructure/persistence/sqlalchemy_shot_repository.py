from __future__ import annotations

from typing import Any

from sqlalchemy import ColumnElement, and_, case, func, select
from sqlalchemy.orm import Session

from player_scouting.application.ports import (
    MatchRef,
    Partnership,
    PlayerShot,
    ShotLeader,
    ShotMetric,
)
from player_scouting.domain.entities import Player
from player_scouting.domain.shots import GOAL, LATE_MINUTE, Shot, is_outside_box
from player_scouting.infrastructure.persistence.models import (
    PlayerModel,
    ShotModel,
    UnderstatMatchModel,
)

# Per-shot rates are noise below this many (non-penalty) shots.
MINIMUM_SHOTS_FOR_RATES = 10
SET_PIECES = ("FromCorner", "SetPiece", "DirectFreekick")
PENALTY = "Penalty"

S = ShotModel
M = UnderstatMatchModel


def _count(condition: ColumnElement[bool]) -> ColumnElement[Any]:
    return func.sum(case((condition, 1), else_=0))


_goal = S.result == GOAL
_open = S.situation != PENALTY
_np_goals = _count(and_(_goal, _open))
_np_shots = _count(_open)
_np_xg = func.sum(case((_open, S.xg), else_=0.0))
_team = case((S.home, M.home_team), else_=M.away_team)
_opponent = case((S.home, M.away_team), else_=M.home_team)

_METRICS: dict[str, ColumnElement[Any]] = {
    "late_goals": _count(and_(_goal, S.minute >= LATE_MINUTE)),
    "decisive_goals": _count(and_(_goal, S.decisive)),
    "late_decisive_goals": _count(and_(_goal, S.decisive, S.minute >= LATE_MINUTE)),
    "headed_goals": _count(and_(_goal, S.shot_type == "Head")),
    "outside_box_goals": _count(and_(_goal, S.outside_box)),
    "set_piece_goals": _count(and_(_goal, S.situation.in_(SET_PIECES))),
    "finishing": _np_goals - _np_xg,
    "npxg_per_shot": _np_xg / func.nullif(_np_shots, 0),
}


class SqlAlchemyShotRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def known_match_ids(self, season_label: str) -> set[int]:
        rows = self._session.execute(
            select(M.match_id).where(M.season_label == season_label)
        )
        return {row[0] for row in rows}

    def save_match(self, match: MatchRef, shots: list[Shot]) -> None:
        self._session.merge(
            M(
                match_id=match.match_id,
                competition=match.competition,
                season_label=match.season_label,
                played_on=match.played_on,
                home_team=match.home_team,
                away_team=match.away_team,
            )
        )
        self._session.query(S).filter(S.match_id == match.match_id).delete()
        self._session.add_all(
            S(
                shot_id=shot.shot_id,
                match_id=match.match_id,
                understat_player_id=shot.understat_player_id,
                player_name=shot.player_name,
                minute=shot.minute,
                result=shot.result,
                x=shot.x,
                y=shot.y,
                xg=shot.xg,
                situation=shot.situation,
                shot_type=shot.shot_type,
                home=shot.home,
                assisted_by=shot.assisted_by,
                decisive=shot.decisive,
                outside_box=is_outside_box(shot.x, shot.y),
            )
            for shot in shots
        )
        self._session.flush()

    def list_shot_leaders(
        self,
        season_label: str,
        metric: ShotMetric,
        limit: int,
        competition: str | None = None,
    ) -> list[ShotLeader]:
        value = _METRICS[metric]
        statement = (
            select(
                PlayerModel,
                M.competition,
                func.max(_team),
                value.label("value"),
                _np_goals,
                _np_shots,
            )
            .select_from(S)
            .join(M, M.match_id == S.match_id)
            .join(PlayerModel, PlayerModel.understat_id == S.understat_player_id)
            .where(M.season_label == season_label)
            .group_by(PlayerModel.player_id, M.competition)
            .order_by(value.desc(), PlayerModel.name)
            .limit(limit)
        )
        if competition is not None:
            statement = statement.where(M.competition == competition)
        if metric == "npxg_per_shot":
            statement = statement.having(_np_shots >= MINIMUM_SHOTS_FOR_RATES)
        elif metric == "finishing":
            # Goals minus xG can be negative: rank everyone who has shot.
            statement = statement.having(_np_shots > 0)
        else:
            statement = statement.having(value > 0)
        return [
            ShotLeader(
                player=_player(model),
                competition=league,
                team=team,
                value=float(amount),
                goals=int(goals or 0),
                shots=int(shots or 0),
            )
            for model, league, team, amount, goals, shots in self._session.execute(
                statement
            )
        ]

    def list_player_shots(
        self, player_id: int, season_label: str | None = None
    ) -> list[PlayerShot]:
        statement = (
            select(S, M.competition, M.season_label, _team, _opponent, M.played_on)
            .join(M, M.match_id == S.match_id)
            .join(PlayerModel, PlayerModel.understat_id == S.understat_player_id)
            .where(PlayerModel.player_id == player_id)
            .order_by(M.played_on, S.minute)
        )
        if season_label is not None:
            statement = statement.where(M.season_label == season_label)
        rows = self._session.execute(statement)
        return [
            PlayerShot(
                shot=_shot(model),
                competition=league,
                season_label=label,
                team=team,
                opponent=opponent,
                played_on=played_on,
            )
            for model, league, label, team, opponent, played_on in rows
        ]

    def list_partnerships(
        self, season_label: str, limit: int, competition: str | None = None
    ) -> list[Partnership]:
        goals = func.count(S.shot_id)
        statement = (
            select(PlayerModel, S.assisted_by, func.max(_team), M.competition, goals)
            .select_from(S)
            .join(M, M.match_id == S.match_id)
            .join(PlayerModel, PlayerModel.understat_id == S.understat_player_id)
            .where(M.season_label == season_label, _goal, S.assisted_by.is_not(None))
            .group_by(PlayerModel.player_id, S.assisted_by, M.competition)
            .order_by(goals.desc(), PlayerModel.name)
            .limit(limit)
        )
        if competition is not None:
            statement = statement.where(M.competition == competition)
        rows = list(self._session.execute(statement))
        assisters = self._players_by_name({row[1] for row in rows})
        return [
            Partnership(
                scorer=_player(model),
                assister_name=assister,
                assister=assisters.get(assister),
                team=team,
                competition=league,
                goals=int(count),
            )
            for model, assister, team, league, count in rows
        ]

    def _players_by_name(self, names: set[str]) -> dict[str, Player]:
        """Understat-linked players with exactly that name; ambiguous ones left out."""
        found: dict[str, list[PlayerModel]] = {}
        for model in self._session.scalars(
            select(PlayerModel).where(
                PlayerModel.name.in_(names), PlayerModel.understat_id.is_not(None)
            )
        ):
            found.setdefault(model.name, []).append(model)
        return {
            name: _player(models[0])
            for name, models in found.items()
            if len(models) == 1
        }


def _player(model: PlayerModel) -> Player:
    return Player(
        model.player_id,
        model.name,
        model.position,
        model.date_of_birth,
        photo_url=model.photo_url,
        preferred_foot=model.preferred_foot,
        birth_year=model.birth_year,
    )


def _shot(model: ShotModel) -> Shot:
    return Shot(
        shot_id=model.shot_id,
        match_id=model.match_id,
        understat_player_id=model.understat_player_id,
        player_name=model.player_name,
        minute=model.minute,
        result=model.result,
        x=model.x,
        y=model.y,
        xg=model.xg,
        situation=model.situation,
        shot_type=model.shot_type,
        home=model.home,
        assisted_by=model.assisted_by,
        decisive=model.decisive,
    )

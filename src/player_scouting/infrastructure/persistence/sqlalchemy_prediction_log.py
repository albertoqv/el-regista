from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from player_scouting.application.ports import PredictionSnapshot
from player_scouting.infrastructure.persistence.models import PredictionSnapshotModel


def _to_domain(model: PredictionSnapshotModel) -> PredictionSnapshot:
    market = (
        (model.market_home, model.market_draw, model.market_away)
        if model.market_home is not None
        and model.market_draw is not None
        and model.market_away is not None
        else None
    )
    return PredictionSnapshot(
        match_id=model.match_id,
        competition=model.competition,
        season_label=model.season_label,
        kickoff=model.kickoff,
        home_team=model.home_team,
        away_team=model.away_team,
        made_at=model.made_at,
        model=(model.model_home, model.model_draw, model.model_away),
        market=market,
        over_2_5=model.over_2_5,
    )


class SqlAlchemyPredictionLog:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_snapshot(self, snapshot: PredictionSnapshot) -> None:
        market = snapshot.market or (None, None, None)
        self._session.merge(
            PredictionSnapshotModel(
                match_id=snapshot.match_id,
                competition=snapshot.competition,
                season_label=snapshot.season_label,
                kickoff=snapshot.kickoff,
                home_team=snapshot.home_team,
                away_team=snapshot.away_team,
                made_at=snapshot.made_at,
                model_home=snapshot.model[0],
                model_draw=snapshot.model[1],
                model_away=snapshot.model[2],
                market_home=market[0],
                market_draw=market[1],
                market_away=market[2],
                over_2_5=snapshot.over_2_5,
            )
        )
        self._session.commit()

    def list_snapshots(self) -> list[PredictionSnapshot]:
        statement = select(PredictionSnapshotModel).order_by(
            PredictionSnapshotModel.kickoff, PredictionSnapshotModel.match_id
        )
        return [_to_domain(model) for model in self._session.scalars(statement)]

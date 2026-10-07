from __future__ import annotations

import json
from datetime import date

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from player_scouting.application.ports import StoredValueEstimate
from player_scouting.domain.valuation import ValuationReport, ValueFactor
from player_scouting.infrastructure.persistence.models import (
    PlayerValueEstimateModel,
    ValueModelModel,
)

# Rows per INSERT: one round trip each, whatever the number of players.
BATCH = 2000


class SqlAlchemyValueEstimateRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_value_estimates(self, report: ValuationReport, computed_on: date) -> None:
        self._session.execute(delete(PlayerValueEstimateModel))
        rows = [
            {
                "player_id": estimate.player_id,
                "estimate_eur": estimate.estimate_eur,
                "factors": json.dumps(
                    [[factor.label, factor.factor] for factor in estimate.factors]
                ),
                "computed_on": computed_on,
            }
            for estimate in report.estimates
        ]
        for start in range(0, len(rows), BATCH):
            self._session.execute(
                insert(PlayerValueEstimateModel), rows[start : start + BATCH]
            )
        self._session.merge(
            ValueModelModel(
                id=1,
                computed_on=computed_on,
                samples=report.samples,
                median_error=report.median_error,
                average_eur=report.average_eur,
            )
        )
        self._session.commit()

    def get_value_estimate(self, player_id: int) -> StoredValueEstimate | None:
        model = self._session.get(PlayerValueEstimateModel, player_id)
        if model is None:
            return None
        return _to_domain(model, self._session.get(ValueModelModel, 1))

    def list_value_estimates(self) -> list[StoredValueEstimate]:
        run = self._session.get(ValueModelModel, 1)
        return [
            _to_domain(model, run)
            for model in self._session.scalars(select(PlayerValueEstimateModel))
        ]


def _to_domain(
    model: PlayerValueEstimateModel, run: ValueModelModel | None
) -> StoredValueEstimate:
    return StoredValueEstimate(
        player_id=model.player_id,
        estimate_eur=model.estimate_eur,
        factors=tuple(
            ValueFactor(label, factor) for label, factor in json.loads(model.factors)
        ),
        computed_on=model.computed_on,
        samples=run.samples if run else 0,
        median_error=run.median_error if run else 0.0,
    )

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import distinct, func, select, tuple_
from sqlalchemy.orm import Session

from player_scouting.application.ports import DailyVisits, PageView, RankedCount
from player_scouting.infrastructure.persistence.models import PageViewModel


class SqlAlchemyVisitRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_page_view(self, view: PageView) -> None:
        self._session.add(
            PageViewModel(
                day=view.day,
                path=view.path,
                visitor=view.visitor,
                referrer=view.referrer,
            )
        )
        self._session.commit()

    def daily_visits(self, since: date) -> list[DailyVisits]:
        rows = self._session.execute(
            select(
                PageViewModel.day,
                func.count(),
                func.count(distinct(PageViewModel.visitor)),
            )
            .where(PageViewModel.day >= since)
            .group_by(PageViewModel.day)
            .order_by(PageViewModel.day)
        ).all()
        return [DailyVisits(day, views, visitors) for day, views, visitors in rows]

    def _ranked(self, column: Any, since: date, limit: int) -> list[RankedCount]:
        views = func.count()
        rows = self._session.execute(
            select(
                column,
                views,
                func.count(distinct(tuple_(PageViewModel.day, PageViewModel.visitor))),
            )
            .where(PageViewModel.day >= since, column.is_not(None))
            .group_by(column)
            .order_by(views.desc(), column)
            .limit(limit)
        ).all()
        return [RankedCount(name, count, people) for name, count, people in rows]

    def top_pages(self, since: date, limit: int) -> list[RankedCount]:
        return self._ranked(PageViewModel.path, since, limit)

    def top_referrers(self, since: date, limit: int) -> list[RankedCount]:
        return self._ranked(PageViewModel.referrer, since, limit)

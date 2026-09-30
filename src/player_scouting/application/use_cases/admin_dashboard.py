from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from urllib.parse import urlsplit

from player_scouting.application.ports import (
    DailyVisits,
    HostingUsage,
    HostingUsageProvider,
    PageView,
    RankedCount,
    VisitRepository,
)

_BOT = re.compile(
    r"bot|crawl|spider|slurp|headless|lighthouse|preview|externalhit|monitor|"
    r"curl|wget|python|httpx|axios|node-fetch|go-http|java/",
    re.IGNORECASE,
)
PRIVATE_PATHS = ("/admin",)
MAX_PATH_LENGTH = 200


def is_bot(user_agent: str) -> bool:
    return not user_agent.strip() or bool(_BOT.search(user_agent))


def _referrer_host(referrer: str | None, own_hosts: tuple[str, ...]) -> str | None:
    if not referrer:
        return None
    host = (urlsplit(referrer).hostname or "").lower().removeprefix("www.")
    if not host or host in own_hosts or host in ("localhost", "127.0.0.1"):
        return None
    return host


class RecordVisitUseCase:
    """Counts people, not requests: bots are skipped and no IP is stored.

    The visitor id is a hash of IP + browser + day + a secret salt, so the same
    person counts once a day and cannot be followed from one day to the next
    (the approach of privacy-first analytics: no cookies, no banner needed).
    """

    def __init__(
        self,
        repository: VisitRepository,
        salt: str,
        today: Callable[[], date] = date.today,
        own_hosts: tuple[str, ...] = (),
    ) -> None:
        self._repository = repository
        self._salt = salt
        self._today = today
        self._own_hosts = tuple(host.removeprefix("www.") for host in own_hosts)

    def execute(
        self, path: str, referrer: str | None, ip: str, user_agent: str
    ) -> bool:
        clean_path = urlsplit(path).path[:MAX_PATH_LENGTH] or "/"
        if is_bot(user_agent) or clean_path.startswith(PRIVATE_PATHS):
            return False
        day = self._today()
        visitor = hashlib.sha256(
            f"{self._salt}|{day.isoformat()}|{ip}|{user_agent}".encode()
        ).hexdigest()[:16]
        self._repository.save_page_view(
            PageView(
                day, clean_path, visitor, _referrer_host(referrer, self._own_hosts)
            )
        )
        return True


@dataclass(frozen=True)
class AdminDashboard:
    days: int
    views_today: int
    visitors_today: int
    views_period: int
    visitors_period: int
    daily: list[DailyVisits]
    top_pages: list[RankedCount]
    top_referrers: list[RankedCount]
    hosting: HostingUsage | None
    hosting_error: str | None


class AdminDashboardUseCase:
    def __init__(
        self,
        visits: VisitRepository,
        hosting: HostingUsageProvider | None,
        today: Callable[[], date] = date.today,
    ) -> None:
        self._visits = visits
        self._hosting = hosting
        self._today = today

    def execute(self, days: int = 30) -> AdminDashboard:
        today = self._today()
        since = today - timedelta(days=days - 1)
        by_day = {row.day: row for row in self._visits.daily_visits(since)}
        daily = [
            by_day.get(day, DailyVisits(day, 0, 0))
            for day in (since + timedelta(days=offset) for offset in range(days))
        ]
        hosting, hosting_error = self._hosting_usage()
        return AdminDashboard(
            days=days,
            views_today=daily[-1].views,
            visitors_today=daily[-1].visitors,
            views_period=sum(row.views for row in daily),
            visitors_period=sum(row.visitors for row in daily),
            daily=daily,
            top_pages=self._visits.top_pages(since, 15),
            top_referrers=self._visits.top_referrers(since, 10),
            hosting=hosting,
            hosting_error=hosting_error,
        )

    def _hosting_usage(self) -> tuple[HostingUsage | None, str | None]:
        if self._hosting is None:
            return None, None
        try:
            return self._hosting.current_usage(), None
        except Exception as error:  # noqa: BLE001 - the panel must still load
            return None, str(error) or type(error).__name__

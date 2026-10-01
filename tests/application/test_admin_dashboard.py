from datetime import date, datetime

from player_scouting.application.ports import HostingUsage
from player_scouting.application.use_cases.admin_dashboard import (
    AdminDashboardUseCase,
    RecordVisitUseCase,
    is_bot,
)
from tests.application.doubles import InMemoryVisitRepository

CHROME = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)


def _recorder(repository, day=date(2026, 9, 30)):
    return RecordVisitUseCase(repository, salt="s3cret", today=lambda: day)


def test_a_visit_is_stored_without_the_ip_and_with_only_the_referrer_host():
    repository = InMemoryVisitRepository()

    recorded = _recorder(repository).execute(
        path="/players/7?sc=La%20Liga",
        referrer="https://www.google.com/search?q=yamal",
        ip="81.0.0.1",
        user_agent=CHROME,
    )

    assert recorded
    [view] = repository.views
    assert view.path == "/players/7"
    assert view.referrer == "google.com"
    assert "81.0.0.1" not in view.visitor
    assert len(view.visitor) == 16


def test_the_same_person_counts_once_per_day_and_changes_the_next_day():
    repository = InMemoryVisitRepository()

    for path in ("/", "/gemelos"):
        _recorder(repository).execute(path, None, "81.0.0.1", CHROME)
    _recorder(repository, date(2026, 10, 1)).execute("/", None, "81.0.0.1", CHROME)

    first, second, third = (view.visitor for view in repository.views)
    assert first == second
    assert third != first


def test_bots_and_our_own_admin_page_are_not_counted():
    repository = InMemoryVisitRepository()
    recorder = _recorder(repository)

    assert not recorder.execute("/", None, "1.1.1.1", "Googlebot/2.1")
    assert not recorder.execute("/", None, "1.1.1.1", "HeadlessChrome/140")
    assert not recorder.execute("/admin", None, "1.1.1.1", CHROME)
    assert repository.views == []


def test_is_bot_recognises_crawlers_and_empty_agents():
    assert is_bot("")
    assert is_bot("facebookexternalhit/1.1")
    assert is_bot("python-httpx/0.28")
    assert not is_bot(CHROME)


def test_own_site_referrers_are_dropped():
    repository = InMemoryVisitRepository()
    RecordVisitUseCase(
        repository,
        salt="s",
        today=lambda: date(2026, 9, 30),
        own_hosts=("elregista.vercel.app",),
    ).execute("/", "https://elregista.vercel.app/gemelos", "1.1.1.1", CHROME)

    assert repository.views[0].referrer is None


class FakeHosting:
    def __init__(self, usage=None, error=None):
        self.usage = usage
        self.error = error

    def current_usage(self):
        if self.error:
            raise self.error
        return self.usage


def _dashboard(repository, hosting=None):
    return AdminDashboardUseCase(
        repository, hosting, today=lambda: date(2026, 9, 30)
    ).execute(days=30)


def test_dashboard_sums_views_and_daily_visitors_and_ranks_pages():
    repository = InMemoryVisitRepository()
    recorder = _recorder(repository)
    for ip, path in [("a", "/"), ("a", "/gemelos"), ("b", "/"), ("c", "/gemelos")]:
        recorder.execute(path, "https://t.co/x", ip, CHROME)
    _recorder(repository, date(2026, 9, 29)).execute("/", None, "a", CHROME)
    _recorder(repository, date(2026, 8, 1)).execute("/", None, "old", CHROME)

    dashboard = _dashboard(repository)

    assert dashboard.views_today == 4
    assert dashboard.visitors_today == 3
    assert dashboard.views_period == 5
    assert dashboard.visitors_period == 4  # sum of daily unique visitors
    assert [(day.day, day.views) for day in dashboard.daily][-2:] == [
        (date(2026, 9, 29), 1),
        (date(2026, 9, 30), 4),
    ]
    # Every day of the window is present, even with no visits.
    assert len(dashboard.daily) == 30
    assert [(p.name, p.views) for p in dashboard.top_pages] == [
        ("/", 3),
        ("/gemelos", 2),
    ]
    assert dashboard.top_referrers[0].name == "t.co"
    assert dashboard.hosting is None
    assert dashboard.hosting_error is None


def test_dashboard_includes_hosting_costs_and_survives_their_failure():
    usage = HostingUsage(
        period_start=datetime(2026, 9, 29),
        period_end=datetime(2026, 10, 29),
        current_dollars=0.14,
        estimated_dollars=3.1,
        line_items={"Memoria": 0.12, "CPU": 0.01},
        usage_limit_dollars=None,
    )

    ok = _dashboard(InMemoryVisitRepository(), FakeHosting(usage))
    broken = _dashboard(
        InMemoryVisitRepository(), FakeHosting(error=RuntimeError("401"))
    )

    assert ok.hosting == usage
    assert broken.hosting is None
    assert broken.hosting_error == "401"

from player_scouting.domain.season import Season
from player_scouting.infrastructure.fbref_kaggle.provider import (
    FbrefKaggleSeasonProvider,
)

CSV_TEXT = (
    "Rk,Player,Pos,Squad,Comp,Born,Gls,Ast\n"
    "1,Jude Bellingham,MF,Real Madrid,es La Liga,2003.0,3,2\n"
)


class FakeClient:
    def __init__(self) -> None:
        self.requested_years: list[int] = []

    def download_season_csv(self, start_year: int) -> str:
        self.requested_years.append(start_year)
        return CSV_TEXT


def test_downloads_the_requested_season_and_maps_its_rows():
    client = FakeClient()
    provider = FbrefKaggleSeasonProvider(client)

    results = provider.get_season(2026)

    assert client.requested_years == [2026]
    assert len(results) == 1
    assert results[0].name == "Jude Bellingham"
    assert results[0].season == Season("La Liga", "2026")
    assert results[0].statistics.goals == 3

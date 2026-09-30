from datetime import date

from player_scouting.application.use_cases.merge_duplicate_players import (
    choose_kept,
)
from player_scouting.domain.entities import Player


def test_keeps_the_record_with_a_photo_and_the_most_recent_season():
    old = Player(1, "Che Adams", "Forward", None, birth_year=1996)
    new = Player(2, "Ché Adams", "Forward", None, birth_year=1996)
    with_photo = Player(
        3, "Che Adams", "Forward", date(1996, 7, 13), photo_url="https://x/p.jpg"
    )

    assert choose_kept([(old, 2024), (new, 2026)]) == new
    assert choose_kept([(with_photo, 2024), (new, 2026)]) == with_photo

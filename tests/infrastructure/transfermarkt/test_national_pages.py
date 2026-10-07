# ruff: noqa: E501 - fixtures are real HTML, kept as served.
from player_scouting.infrastructure.transfermarkt.national_pages import (
    CompetitionOption,
    extract_competition_options,
    national_line_label,
)

# Shape captured from Spain's performance page (Oct 2026),
# https://www.transfermarkt.com/spanien/leistungsdaten/verein/3375/plus/1
# (the competition selector: one "Total" per season, then each competition).
SELECTOR_HTML = """
<select name="reldata" data-placeholder="Wählen" class="chzn-select" tabindex="0">
                                            <optgroup label="26/27">
                                                <option value="&2026">Total 26/27</option>
                                                <option value="UNLA&2026">UEFA Nations League A 26/27</option>
                                                                                                </optgroup>
                                            <optgroup label="25/26">
                                                <option  selected="selected"value="&2025">Total 25/26</option>
                                                <option value="AFT&2025">CONMEBOL-UEFA Cup of Champions 25/26</option>
                                                <option value="FS&2025">International Friendlies 25/26</option>
                                                <option value="FIWC&2025">World Cup 25/26</option>
                                                </optgroup>
                                            <optgroup label="24/25">
                                                <option value="WMQ6&2024">World Cup Qualifiers (Europe) 24/25</option>
                                                <option value="EURO&2023">UEFA Euro 23/24</option>
                                                </optgroup>
</select>
"""


def test_reads_every_competition_of_the_national_team_but_the_totals():
    assert extract_competition_options(SELECTOR_HTML) == [
        CompetitionOption("UNLA", 2026, "UEFA Nations League A"),
        CompetitionOption("AFT", 2025, "CONMEBOL-UEFA Cup of Champions"),
        CompetitionOption("FS", 2025, "International Friendlies"),
        CompetitionOption("FIWC", 2025, "World Cup"),
        CompetitionOption("WMQ6", 2024, "World Cup Qualifiers (Europe)"),
        CompetitionOption("EURO", 2023, "UEFA Euro"),
    ]


def test_tournaments_are_named_by_their_year_and_the_rest_by_season():
    # A finals tournament is played in the summer after the season starts.
    assert national_line_label(CompetitionOption("FIWC", 2025, "World Cup")) == (
        "Mundial",
        "2026",
    )
    assert national_line_label(CompetitionOption("EURO", 2023, "UEFA Euro")) == (
        "Eurocopa",
        "2024",
    )
    assert national_line_label(
        CompetitionOption("UNLA", 2026, "UEFA Nations League A")
    ) == ("Nations League A", "2026")
    assert national_line_label(
        CompetitionOption("WMQ6", 2024, "World Cup Qualifiers (Europe)")
    ) == ("Clasificación Mundial", "2024")
    assert national_line_label(
        CompetitionOption("FS", 2025, "International Friendlies")
    ) == ("Amistosos", "2025")


def test_other_confederations_follow_the_same_rules():
    # Codes on Argentina's page (Oct 2026).
    assert national_line_label(CompetitionOption("COPA", 2023, "Copa América")) == (
        "Copa América",
        "2024",
    )
    assert national_line_label(
        CompetitionOption("WMQ4", 2024, "World Cup qualification South America")
    ) == ("Clasificación Mundial", "2024")


def test_an_unknown_competition_keeps_its_transfermarkt_name():
    option = CompetitionOption("XYZ", 2025, "Some Invitational Cup")

    assert national_line_label(option) == ("Some Invitational Cup", "2025")

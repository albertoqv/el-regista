import pytest

from player_scouting.domain.exceptions import InvalidStatisticsError
from player_scouting.domain.statistics import Statistics


def test_estadisticas_guarda_sus_datos_correctamente():
    resultado = Statistics(15, 20)
    assert resultado.goals == 15
    assert resultado.assists == 20


def test_estadisticas_rechaza_un_valor_de_goles_no_entero():
    with pytest.raises(InvalidStatisticsError):
        Statistics(15.5, 20)


def test_estadisticas_rechaza_un_valor_de_asistencias_no_entero():
    with pytest.raises(InvalidStatisticsError):
        Statistics(15, 20.5)


def test_estadisticas_goles_es_inferior_al_rango():
    with pytest.raises(InvalidStatisticsError):
        Statistics(-1, 20)


def test_estadisticas_asistencias_es_inferior_al_rango():
    with pytest.raises(InvalidStatisticsError):
        Statistics(20, -1)


def test_estadisticas_rechaza_un_valor_de_goles_booleano():
    with pytest.raises(InvalidStatisticsError):
        Statistics(True, 20)


def test_estadisticas_rechaza_un_valor_de_asistencias_booleano():
    with pytest.raises(InvalidStatisticsError):
        Statistics(15, True)


def test_estadisticas_las_metricas_extendidas_valen_cero_por_defecto():
    resultado = Statistics(15, 20)

    assert resultado.shots == 0
    assert resultado.shots_on_target == 0
    assert resultado.expected_goals == 0.0
    assert resultado.passes_completed == 0
    assert resultado.passes_attempted == 0
    assert resultado.key_passes == 0
    assert resultado.dribbles_completed == 0
    assert resultado.dribbles_attempted == 0
    assert resultado.tackles_won == 0
    assert resultado.interceptions == 0
    assert resultado.fouls_committed == 0
    assert resultado.fouls_won == 0
    assert resultado.yellow_cards == 0
    assert resultado.red_cards == 0


def test_estadisticas_acepta_todas_las_metricas_extendidas():
    resultado = Statistics(
        goals=1,
        assists=2,
        shots=3,
        shots_on_target=4,
        expected_goals=0.75,
        passes_completed=5,
        passes_attempted=6,
        key_passes=7,
        dribbles_completed=8,
        dribbles_attempted=9,
        tackles_won=10,
        interceptions=11,
        fouls_committed=12,
        fouls_won=13,
        yellow_cards=14,
        red_cards=15,
    )

    assert resultado.shots == 3
    assert resultado.expected_goals == 0.75
    assert resultado.red_cards == 15


@pytest.mark.parametrize(
    "field_name",
    [
        "shots",
        "shots_on_target",
        "passes_completed",
        "passes_attempted",
        "key_passes",
        "dribbles_completed",
        "dribbles_attempted",
        "tackles_won",
        "interceptions",
        "fouls_committed",
        "fouls_won",
        "yellow_cards",
        "red_cards",
    ],
)
def test_estadisticas_rechaza_valores_negativos_en_metricas_extendidas(field_name):
    with pytest.raises(InvalidStatisticsError):
        Statistics(1, 1, **{field_name: -1})


def test_estadisticas_rechaza_expected_goals_negativo():
    with pytest.raises(InvalidStatisticsError):
        Statistics(1, 1, expected_goals=-0.1)


def test_estadisticas_rechaza_expected_goals_no_numerico():
    with pytest.raises(InvalidStatisticsError):
        Statistics(1, 1, expected_goals="0.5")

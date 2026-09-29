import pytest

from player_scouting.domain.similarity_calculator import SimilarityCalculator
from player_scouting.domain.statistics import Statistics
from player_scouting.domain.value_objects import SimilarityScore


def test_similitud_metrica_con_valores_iguales_es_uno():
    calculador = SimilarityCalculator()

    resultado = calculador.similarity_metric(10, 10)

    assert resultado == 1


def test_calcular_similitud_metrica_con_valores_distintos():
    calculador = SimilarityCalculator()
    resultado = calculador.similarity_metric(10, 12)
    assert resultado == pytest.approx(0.833, rel=0.01)


def test_calcular_similitud_total():
    estadistica_j1 = Statistics(10, 15)
    estadistica_j2 = Statistics(15, 10)
    calculador = SimilarityCalculator()
    resultado = calculador.total_similarity(estadistica_j1, estadistica_j2)
    assert resultado == SimilarityScore(67)


def test_similitud_total_tiene_en_cuenta_las_metricas_extendidas():
    estadistica_j1 = Statistics(1, 1, shots=10)
    estadistica_j2 = Statistics(1, 1, shots=5)
    calculador = SimilarityCalculator()

    resultado = calculador.total_similarity(estadistica_j1, estadistica_j2)

    assert resultado == SimilarityScore(83)


def test_similitud_total_ignora_metricas_en_las_que_ambos_estan_a_cero():
    estadistica_j1 = Statistics(goals=0, assists=0, shots=10)
    estadistica_j2 = Statistics(goals=10, assists=10, shots=10)
    calculador = SimilarityCalculator()

    resultado = calculador.total_similarity(estadistica_j1, estadistica_j2)

    assert resultado == SimilarityScore(33)


def test_similitud_total_es_cien_cuando_todas_las_metricas_estan_a_cero():
    estadistica_j1 = Statistics(0, 0)
    estadistica_j2 = Statistics(0, 0)
    calculador = SimilarityCalculator()

    resultado = calculador.total_similarity(estadistica_j1, estadistica_j2)

    assert resultado == SimilarityScore(100)


def test_similitud_total_no_compara_los_minutos_jugados():
    calculadora = SimilarityCalculator()
    mismo_estilo_distintos_minutos = calculadora.total_similarity(
        Statistics(10, 5, minutes_played=900),
        Statistics(10, 5, minutes_played=2700),
    )

    assert mismo_estilo_distintos_minutos.percentage == 100

"""T-018 · Valores imposibles (RF-100, RF-101) y logos (RF-130)."""

from decimal import Decimal

import pytest

from app.domain.validation import (
    is_valid_logo_url,
    is_valid_maps_won,
    is_valid_non_negative,
    is_valid_pool_percent,
    maps_needed_to_win,
)


@pytest.mark.parametrize("value", [-1, -0.5, Decimal("-1.20")])
def test_estadistica_marcador_kd_o_premio_negativos_no_son_validos(value):
    assert not is_valid_non_negative(value)


@pytest.mark.parametrize("value", [0, 0.0, 25, Decimal("1.250"), 800000])
def test_cero_y_positivos_son_validos(value):
    # 0 es un valor real ("no lo hizo"), no una ausencia.
    assert is_valid_non_negative(value)


@pytest.mark.parametrize("value", ["25", True, None, [1]])
def test_lo_que_no_es_un_numero_no_es_valido(value):
    assert not is_valid_non_negative(value)


@pytest.mark.parametrize("value", [-0.1, 100.01, Decimal("150")])
def test_porcentaje_fuera_de_0_a_100_no_es_valido(value):
    assert not is_valid_pool_percent(value)


@pytest.mark.parametrize("value", [0, 40, Decimal("12.5"), 100])
def test_porcentaje_entre_0_y_100_es_valido(value):
    assert is_valid_pool_percent(value)


def test_mapas_necesarios_para_ganar():
    assert maps_needed_to_win(5) == 3
    assert maps_needed_to_win(3) == 2
    assert maps_needed_to_win(7) == 4


def test_al_mejor_de_5_cuatro_mapas_ganados_no_es_valido_y_tres_si():
    assert not is_valid_maps_won(4, best_of=5)
    assert is_valid_maps_won(3, best_of=5)
    assert is_valid_maps_won(0, best_of=5)
    assert not is_valid_maps_won(-1, best_of=5)


@pytest.mark.parametrize(
    "url",
    [
        "https://cdn.example.com/logos/team.png",
        "https://cdn.example.com/logos/team.SVG",
        "https://cdn.example.com/a/b/team.webp?version=3",
        "https://cdn.example.com/team.jpeg",
    ],
)
def test_logo_https_con_extension_de_imagen_es_valido(url):
    assert is_valid_logo_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://cdn.example.com/team.png",
        "javascript:alert(1)",
        "https://cdn.example.com/team",
        "https://cdn.example.com/team.html",
        "data:image/png;base64,AAAA",
        "https:///team.png",
        "",
        None,
        42,
    ],
)
def test_logo_que_no_es_https_o_no_es_imagen_no_es_valido(url):
    assert not is_valid_logo_url(url)

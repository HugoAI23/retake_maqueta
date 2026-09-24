"""T-017 · Marcador en vivo más avanzado (RF-57 a RF-59)."""

from app.domain.live_score import LiveScore, SourceScore, most_advanced


def s(source, maps, live=None):
    return SourceScore(source, LiveScore(maps, live))


def test_gana_el_que_tiene_mas_mapas_terminados_aunque_sea_de_una_fuente_secundaria():
    result = most_advanced([s("bp", (1, 1), (100, 80)), s("wiki", (2, 1), (0, 0))], registered=None)
    assert result == LiveScore((2, 1), (0, 0))


def test_con_los_mismos_mapas_gana_el_que_suma_mas_en_el_mapa_en_curso():
    result = most_advanced([s("bp", (1, 0), (120, 90)), s("cdl", (1, 0), (130, 95))], registered=None)
    assert result == LiveScore((1, 0), (130, 95))


def test_un_marcador_del_mapa_en_curso_ausente_pierde_ante_uno_publicado():
    result = most_advanced([s("bp", (1, 0), None), s("wiki", (1, 0), (0, 5))], registered=None)
    assert result == LiveScore((1, 0), (0, 5))


def test_nunca_retrocede_respecto_a_lo_registrado():
    registered = LiveScore((2, 1), (40, 30))
    # La fuente principal va por detrás: se conserva lo registrado (RF-59).
    assert most_advanced([s("bp", (2, 1), (20, 10))], registered=registered) == registered
    assert most_advanced([s("bp", (1, 1), (240, 200))], registered=registered) == registered


def test_avanza_respecto_a_lo_registrado_cuando_llega_algo_mas_avanzado():
    registered = LiveScore((2, 1), (240, 200))
    # Empieza un mapa nuevo: más mapas terminados aunque el mapa en curso vaya 0-0.
    assert most_advanced([s("bp", (3, 1), (0, 0))], registered=registered) == LiveScore((3, 1), (0, 0))


def test_empate_exacto_entre_fuentes_se_resuelve_por_la_prioridad():
    # Mismo avance, distinto reparto: manda BreakingPoint > Wiki > CDL.
    result = most_advanced([s("cdl", (2, 1), (10, 5)), s("bp", (1, 2), (5, 10))], registered=None)
    assert result == LiveScore((1, 2), (5, 10))


def test_sin_ningun_marcador_se_conserva_lo_registrado():
    registered = LiveScore((0, 0), None)
    assert most_advanced([], registered=registered) == registered
    assert most_advanced([], registered=None) is None

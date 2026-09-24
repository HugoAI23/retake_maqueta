"""T-046 · Cuándo un partido finalizado tiene todas sus estadísticas (spec 003: RF-19, RF-20).

Criterio de RF-47 de la 002: están todas cuando ningún mapa jugado tiene un jugador al que
le falten todas sus estadísticas. Un mapa jugado sin ninguna estadística también las tiene
pendientes. Una estadística suelta ausente no las deja pendientes (RF-72 de la 002).
"""

from datetime import UTC, datetime, timedelta

from tests.integration.ingest.helpers import rec
from tests.integration.ingest.test_matches import base, get_match, match

NOW = datetime(2026, 1, 11, 12, 0, tzinfo=UTC)


def played_map(position, **fields):
    return rec("match_map", f"mp{position}", match_ref="bp:m1", position=position, mode="Hardpoint",
               status="played", score=[250, 200], winner_side=1, **fields)


def stats(sid, map_ref, player="p1", **values):
    return rec("player_map_stats", sid, map_ref=map_ref, player_ref=f"bp:{player}", franchise_ref="bp:t1", **values)


def players():
    return [rec("player", "p1", gamertag="[FICTICIO] Uno"), rec("player", "p2", gamertag="[FICTICIO] Dos")]


def test_un_forfeit_sin_mapas_tiene_sus_estadisticas_desde_que_finaliza(session, ingest):
    ingest([*base(), match(status="finished", maps_won=[3, 0])], now=NOW)
    assert get_match(session).stats_complete_at == NOW


def test_un_partido_sin_finalizar_no_tiene_la_marca(session, ingest):
    ingest([*base(), match(status="live")], now=NOW)
    assert get_match(session).stats_complete_at is None


def test_un_mapa_jugado_sin_estadisticas_las_deja_pendientes(session, ingest):
    ingest([*base(), *players(), match(status="finished", maps_won=[3, 0]), played_map(1)], now=NOW)
    assert get_match(session).stats_complete_at is None


def test_un_jugador_sin_ninguna_estadistica_las_deja_pendientes(session, ingest):
    ingest([*base(), *players(), match(status="finished", maps_won=[3, 0]), played_map(1),
            stats("a", "bp:mp1", kills=10, deaths=8), stats("b", "bp:mp1", player="p2")], now=NOW)
    assert get_match(session).stats_complete_at is None


def test_una_estadistica_suelta_ausente_no_las_deja_pendientes(session, ingest):
    ingest([*base(), *players(), match(status="finished", maps_won=[3, 0]), played_map(1),
            stats("a", "bp:mp1", kills=10), stats("b", "bp:mp1", player="p2", deaths=4)], now=NOW)
    assert get_match(session).stats_complete_at == NOW


def test_la_marca_se_fija_cuando_llegan_y_no_se_mueve_al_reingerir(session, ingest):
    ingest([*base(), *players(), match(status="finished", maps_won=[3, 0]), played_map(1)], now=NOW)
    later = NOW + timedelta(hours=1)
    ingest([stats("a", "bp:mp1", hours=1, kills=10)], now=later)
    assert get_match(session).stats_complete_at == later
    ingest([stats("a", "bp:mp1", hours=2, kills=11)], now=later + timedelta(hours=1))
    assert get_match(session).stats_complete_at == later


def test_si_vuelven_a_faltar_la_marca_se_retira(session, ingest):
    ingest([*base(), *players(), match(status="finished", maps_won=[3, 0]), played_map(1),
            stats("a", "bp:mp1", kills=10)], now=NOW)
    ingest([stats("b", "bp:mp1", player="p2", hours=1)], now=NOW + timedelta(hours=1))
    assert get_match(session).stats_complete_at is None

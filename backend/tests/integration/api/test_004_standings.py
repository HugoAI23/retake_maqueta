"""F1 de la spec 004 · `/api/standings` con la identidad de cada fila y el balance (T-007, T-008).

- Identidad: la del último partido `en vivo` o `finalizado` de la temporada; sin partidos, la
  vigente (RF-41a, RF-41b).
- Balance: `series` y `maps` de cada fila, o `null` si no está disponible (RF-45, RF-45a; RF-136
  a RF-139 de la 002), y `changedAt` con el cambio más reciente de la fila o de sus partidos
  contados (RF-53e, decisión D-7).
"""

from datetime import timedelta

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.models import Match
from tests.integration.api.test_003_api import T, api, ingest, rec  # noqa: F401 — `api` es un fixture

# El reloj de `api` marca el 2026-01-10 a las 12:30 UTC.


def league():
    return [
        rec("season", "s26", year=2026, name="CDL 2026"),
        rec("event", "e1", season_year=2026, name="[FICTICIO] Major"),
        rec("franchise", "t1"),
        rec("identity", "t1-old", franchise_ref="bp:t1", short_name="[FICTICIO] Breach", abbreviation="BRE",
            valid_from="2021-12-15T00:00:00Z"),
        rec("franchise", "t2"),
        rec("identity", "t2-id", franchise_ref="bp:t2", short_name="[FICTICIO] Dos", valid_from="2021-12-15T00:00:00Z"),
        rec("standing", "st1", season_year=2026, franchise_ref="bp:t1", position=1, points=100),
        rec("standing", "st2", season_year=2026, franchise_ref="bp:t2", position=2, points=80),
    ]


def match(sid, status, when, sides=("bp:t1", "bp:t2"), **fields):
    return rec("match", sid, event_ref="bp:e1", best_of=5, status=status, scheduled_at=when,
               slots=[{"franchise_ref": side} for side in sides], **fields)


def row_names(api):
    return {row["identity"]["shortName"]: row for row in api.get("/api/standings").json()}


# --- T-007 · Identidad de cada fila ------------------------------------------------------------------


def test_la_fila_lleva_la_identidad_de_su_ultimo_partido_y_no_una_posterior(api, clean_db):
    # Caso tipo Boston Breach / M80 Boston: la identidad nueva empieza después del último partido.
    ingest(clean_db, [
        *league(),
        match("m1", "finished", "2026-01-10T11:00:00Z", maps_won=[3, 1], winner_side=1),
        rec("identity", "t1-new", franchise_ref="bp:t1", short_name="[FICTICIO] M80", abbreviation="M80",
            valid_from="2026-01-10T12:00:00Z"),
    ])
    rows = row_names(api)
    assert "[FICTICIO] Breach" in rows
    assert "[FICTICIO] M80" not in rows
    assert rows["[FICTICIO] Breach"]["identity"]["abbreviation"] == "BRE"


def test_un_partido_en_vivo_tambien_cuenta_como_jugado(api, clean_db):
    ingest(clean_db, [
        *league(),
        rec("identity", "t1-new", franchise_ref="bp:t1", short_name="[FICTICIO] M80", valid_from="2026-01-05T00:00:00Z"),
        match("m1", "finished", "2026-01-03T11:00:00Z", maps_won=[3, 1], winner_side=1),
        match("m2", "live", "2026-01-10T12:00:00Z", maps_won=[1, 0]),
    ])
    assert "[FICTICIO] M80" in row_names(api)


def test_un_partido_programado_no_cuenta_como_jugado(api, clean_db):
    ingest(clean_db, [
        *league(),
        match("m1", "finished", "2026-01-03T11:00:00Z", maps_won=[3, 1], winner_side=1),
        rec("identity", "t1-new", franchise_ref="bp:t1", short_name="[FICTICIO] M80", valid_from="2026-01-05T00:00:00Z"),
        match("m2", "scheduled", "2026-01-10T12:00:00Z"),
    ])
    assert "[FICTICIO] Breach" in row_names(api)


def test_una_franquicia_sin_partidos_en_la_temporada_lleva_su_identidad_vigente(api, clean_db):
    # La temporada solo es la actual cuando empieza su primer partido, así que otros equipos juegan.
    ingest(clean_db, [
        *league(),
        match("m1", "finished", "2026-01-03T11:00:00Z", maps_won=[3, 1], winner_side=1),
        rec("franchise", "t3"),
        rec("identity", "t3-old", franchise_ref="bp:t3", short_name="[FICTICIO] Tres antes", valid_from="2021-12-15T00:00:00Z"),
        rec("identity", "t3-new", franchise_ref="bp:t3", short_name="[FICTICIO] Tres", valid_from="2026-01-05T00:00:00Z"),
        rec("standing", "st3", season_year=2026, franchise_ref="bp:t3", position=3, points=10),
    ])
    assert set(row_names(api)) == {"[FICTICIO] Breach", "[FICTICIO] Dos", "[FICTICIO] Tres"}


# --- T-008 · Series, mapas y changedAt ----------------------------------------------------------


def balance(row):
    return row["series"], row["maps"]


def test_cada_fila_lleva_su_balance_de_series_y_mapas(api, clean_db):
    ingest(clean_db, [
        *league(),
        match("m1", "finished", "2026-01-03T11:00:00Z", maps_won=[3, 1], winner_side=1),
        match("m2", "finished", "2026-01-04T11:00:00Z", maps_won=[2, 3], winner_side=2),
        match("m3", "finished", "2026-01-05T11:00:00Z", winner_side=1),        # sin marcador (RF-138)
        match("m4", "finished", "2026-01-06T11:00:00Z"),                       # sin nada (RF-138a)
        match("m5", "live", "2026-01-10T12:00:00Z", maps_won=[1, 0]),          # en vivo: no cuenta
    ])
    rows = row_names(api)
    assert balance(rows["[FICTICIO] Breach"]) == ({"won": 2, "lost": 1}, {"won": 5, "lost": 4})
    assert balance(rows["[FICTICIO] Dos"]) == ({"won": 1, "lost": 2}, {"won": 4, "lost": 5})


def test_los_partidos_contra_un_invitado_cuentan_para_el_equipo_de_la_liga(api, clean_db):
    # Criterio 3a: partido ficticio contra un invitado, creado en la prueba.
    ingest(clean_db, [
        *league(),
        rec("franchise", "g1", guest=True), rec("identity", "g1-id", franchise_ref="bp:g1", short_name="[FICTICIO] Invitado"),
        match("m1", "finished", "2026-01-03T11:00:00Z", sides=("bp:g1", "bp:t1"), maps_won=[1, 3], winner_side=2),
    ])
    rows = row_names(api)
    assert "[FICTICIO] Invitado" not in rows
    assert balance(rows["[FICTICIO] Breach"]) == ({"won": 1, "lost": 0}, {"won": 3, "lost": 1})
    assert balance(rows["[FICTICIO] Dos"]) == ({"won": 0, "lost": 0}, {"won": 0, "lost": 0})


def test_sin_partidos_de_la_temporada_el_balance_no_esta_disponible(api, clean_db):
    # RF-139 de la 002 y D-6: la temporada empezó, pero sus partidos ya no están en los datos.
    ingest(clean_db, [*league(), match("m1", "finished", "2026-01-03T11:00:00Z", maps_won=[3, 1], winner_side=1)])
    with Session(clean_db) as session:
        session.execute(delete(Match))
        session.commit()
    rows = api.get("/api/standings").json()
    assert len(rows) == 2
    assert all(row["series"] is None and row["maps"] is None for row in rows)


def test_changed_at_es_el_cambio_mas_reciente_de_la_fila_o_de_sus_partidos_contados(api, clean_db):
    later = T + timedelta(hours=2)
    ingest(clean_db, [*league(), match("m1", "finished", "2026-01-03T11:00:00Z", maps_won=[3, 1], winner_side=1)])
    # El marcador de m1 cambia más tarde: cambia el balance de los dos equipos.
    ingest(clean_db, [match("m1", "finished", "2026-01-03T11:00:00Z", maps_won=[3, 2], winner_side=1,
                            observed_at=later.isoformat())], now=later)
    # Un partido que no cuenta (sin ganador ni marcador) no cambia la fila.
    ingest(clean_db, [match("m2", "finished", "2026-01-04T11:00:00Z", observed_at=(later + timedelta(hours=1)).isoformat())],
           now=later + timedelta(hours=1))
    rows = row_names(api)
    stamp = later.isoformat().replace("+00:00", "Z")
    assert rows["[FICTICIO] Breach"]["changedAt"] == stamp
    assert rows["[FICTICIO] Dos"]["changedAt"] == stamp


def test_si_la_fila_cambia_despues_que_sus_partidos_manda_la_fila(api, clean_db):
    later = T + timedelta(hours=2)
    ingest(clean_db, [*league(), match("m1", "finished", "2026-01-03T11:00:00Z", maps_won=[3, 1], winner_side=1)])
    ingest(clean_db, [rec("standing", "st1", season_year=2026, franchise_ref="bp:t1", position=1, points=130,
                          observed_at=later.isoformat())], now=later)
    rows = row_names(api)
    assert rows["[FICTICIO] Breach"]["changedAt"] == later.isoformat().replace("+00:00", "Z")
    assert rows["[FICTICIO] Dos"]["changedAt"] != rows["[FICTICIO] Breach"]["changedAt"]

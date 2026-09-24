"""F6 · API ampliada de la spec 003 (T-058 a T-062).

- `changedAt` en cada fila e `isStale` en cada partido (RF-90, RF-157).
- `GET /api/freshness` (RF-89, RF-155, RF-158; C-20).
- `GET /api/logos/{id}` y `logoUrl` a la copia propia (RF-65, RF-70, RF-71).
- Ninguna ruta devuelve datos de la próxima temporada (RF-15).
"""

import io
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from app.api.deps import get_clock
from app.clock import FixedClock
from app.curation.loader import Curation
from app.db.models import DatasetChange, SourceState
from app.ingest.pipeline import ingest_records
from app.logos import fingerprint
from app.main import app, engine_or_none

T = datetime(2026, 1, 10, 12, 0, tzinfo=UTC)
NOW = T + timedelta(minutes=30)


def rec(kind, sid, source="bp", **fields):
    return {"kind": kind, "source": source, "source_id": sid, "observed_at": T.isoformat(), **fields}


@pytest.fixture
def api(clean_db):
    clock = FixedClock(NOW)
    app.dependency_overrides[engine_or_none] = lambda: clean_db
    app.dependency_overrides[get_clock] = lambda: clock
    with TestClient(app) as client:
        client.clock = clock
        yield client
    app.dependency_overrides.clear()


def ingest(engine, records, now=T, logo_fetcher=None):
    with Session(engine) as session:
        report = ingest_records(session, records, curation=Curation(), now=now, logo_fetcher=logo_fetcher)
        session.commit()
    assert report.rejected == []


def set_state(engine, job, success_at, source="bp"):
    with Session(engine) as session:
        session.merge(SourceState(source=source, job=job, last_attempt_at=success_at, last_success_at=success_at))
        session.commit()


def png() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (4, 3), (10, 20, 30)).save(buffer, format="PNG")
    return buffer.getvalue()


def world(match_status="finished", **match_fields):
    return [
        rec("season", "s26", year=2026, name="CDL 2026"),
        rec("event", "e1", season_year=2026, name="[FICTICIO] Major"),
        rec("franchise", "t1"), rec("identity", "t1-id", franchise_ref="bp:t1", short_name="[FICTICIO] Uno"),
        rec("franchise", "t2"), rec("identity", "t2-id", franchise_ref="bp:t2", short_name="[FICTICIO] Dos"),
        rec("player", "p1", gamertag="[FICTICIO] Jugador"),
        rec("standing", "st1", season_year=2026, franchise_ref="bp:t1", position=1, points=100),
        rec("match", "m1", event_ref="bp:e1", best_of=5, status=match_status, scheduled_at="2026-01-10T11:00:00Z",
            slots=[{"franchise_ref": "bp:t1"}, {"franchise_ref": "bp:t2"}], **match_fields),
    ]


# --- T-058 · changedAt e isStale -----------------------------------------------------------------


def test_cada_fila_lleva_changed_at(api, clean_db):
    ingest(clean_db, [*world(maps_won=[3, 0], winner_side=1),
                      rec("match_map", "mp1", match_ref="bp:m1", position=1, mode="Hardpoint", status="played",
                          score=[250, 100], winner_side=1),
                      rec("player_map_stats", "st", map_ref="bp:mp1", player_ref="bp:p1", franchise_ref="bp:t1", kills=20),
                      rec("championship", "c", source="wiki", year=2025, completed=True),
                      rec("placement", "pl", source="wiki", championship_ref="wiki:c", franchise_ref="bp:t1", place="1")])
    stamp = "2026-01-10T12:00:00Z"
    (match,) = api.get("/api/matches").json()
    assert match["changedAt"] == stamp
    assert match["maps"][0]["changedAt"] == stamp and match["maps"][0]["stats"][0]["changedAt"] == stamp
    assert match["slots"][0]["identity"]["changedAt"] == stamp
    assert api.get("/api/season/current").json()["changedAt"] == stamp
    assert api.get("/api/events").json()[0]["changedAt"] == stamp
    assert api.get("/api/players").json()[0]["changedAt"] == stamp
    assert api.get("/api/standings").json()[0]["changedAt"] == stamp
    (championship,) = api.get("/api/championships").json()
    assert championship["changedAt"] == stamp and championship["placements"][0]["changedAt"] == stamp


def test_un_partido_en_vivo_sin_aparecer_mas_de_60_s_esta_sin_actualizar(api, clean_db):
    # RF-90: la fuente consulta con éxito pero el partido ya no aparece.
    ingest(clean_db, world("live"))
    with Session(clean_db) as session:
        from app.ingest.sightings import apply_sightings

        apply_sightings(session, ["bp:m1"], observed_at=T)
        session.commit()
    set_state(clean_db, "live", T + timedelta(seconds=30))
    assert api.get("/api/matches").json()[0]["isStale"] is False
    set_state(clean_db, "live", T + timedelta(seconds=61))
    assert api.get("/api/matches").json()[0]["isStale"] is True


def test_un_partido_que_no_esta_en_vivo_nunca_esta_sin_actualizar(api, clean_db):
    ingest(clean_db, world("finished", maps_won=[3, 1], winner_side=1))
    set_state(clean_db, "regular", T + timedelta(days=3))
    assert api.get("/api/matches").json()[0]["isStale"] is False


# --- T-059 · /api/freshness ----------------------------------------------------------------------


def test_frescura_de_cada_conjunto_de_datos(api, clean_db):
    ingest(clean_db, world("live"))
    set_state(clean_db, "regular", NOW - timedelta(hours=2))   # el "Resto" lleva 2 h sin éxito
    set_state(clean_db, "live", NOW - timedelta(seconds=20))   # el en vivo está al día
    body = api.get("/api/freshness").json()
    assert set(body) == {"live", "matches", "standings", "franchises", "players", "events", "championships", "season"}
    assert body["live"] == {"lastChangedAt": "2026-01-10T12:00:00Z", "stale": False}
    assert body["matches"]["stale"] is True
    assert body["championships"] == {"lastChangedAt": None, "stale": False}  # sin datos y nunca sin actualizar (C-20)


def test_el_en_vivo_solo_puede_estar_sin_actualizar_si_hay_partidos_en_vivo(api, clean_db):
    ingest(clean_db, world("finished", maps_won=[3, 0], winner_side=1))
    set_state(clean_db, "regular", NOW - timedelta(minutes=5))
    set_state(clean_db, "live", NOW - timedelta(hours=5))
    assert api.get("/api/freshness").json()["live"]["stale"] is False


def test_sin_ninguna_consulta_nada_esta_sin_actualizar(api, clean_db):
    # Modo de datos de prueba o carga inicial en curso (RF-8).
    ingest(clean_db, world())
    assert not any(entry["stale"] for entry in api.get("/api/freshness").json().values())


def test_el_historial_nunca_esta_sin_actualizar(api, clean_db):
    with Session(clean_db) as session:
        session.add(DatasetChange(dataset="championships", last_changed_at=T))
        session.merge(SourceState(source="wiki", job="history", last_attempt_at=T, last_success_at=T))
        session.commit()
    api.clock.set(T + timedelta(days=400))
    assert api.get("/api/freshness").json()["championships"] == {"lastChangedAt": "2026-01-10T12:00:00Z", "stale": False}


# --- T-060 · logos --------------------------------------------------------------------------------


def test_el_logo_se_sirve_desde_la_copia_con_sus_cabeceras(api, clean_db):
    image = png()
    ingest(clean_db, [rec("franchise", "t1"), rec("identity", "t1-id", franchise_ref="bp:t1", short_name="[FICTICIO] Uno",
                                                    logo_url="https://ejemplo.com/logo.png")],
           logo_fetcher=lambda url: image)
    identity = api.get("/api/franchises").json()[0]["identities"][0]
    assert identity["logoUrl"] == f"/api/logos/{fingerprint(image)}"
    response = api.get(identity["logoUrl"])
    assert response.status_code == 200 and response.content == image
    assert response.headers["content-type"] == "image/png"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "max-age=31536000" in response.headers["cache-control"] and "immutable" in response.headers["cache-control"]


def test_sin_copia_el_logo_no_esta_registrado(api, clean_db):
    # RF-70: si no se ha podido obtener su imagen, el logo cuenta como no registrado.
    ingest(clean_db, [rec("franchise", "t1"), rec("identity", "t1-id", franchise_ref="bp:t1", short_name="[FICTICIO] Uno",
                                                    logo_url="https://ejemplo.com/logo.png")])
    assert api.get("/api/franchises").json()[0]["identities"][0]["logoUrl"] is None


def test_un_logo_que_no_existe_da_404(api):
    assert api.get(f"/api/logos/{'0' * 64}").status_code == 404
    assert api.get("/api/logos/no-es-una-huella").status_code == 404


# --- T-062 · la próxima temporada no se ve --------------------------------------------------------


def test_ninguna_ruta_devuelve_la_proxima_temporada(api, clean_db):
    ingest(clean_db, [*world("live"),
                      rec("season", "s27", year=2027, name="CDL 2027"),
                      rec("event", "e27", season_year=2027, name="[FICTICIO] Major 2027"),
                      rec("match", "m27", event_ref="bp:e27", best_of=5, status="scheduled",
                          scheduled_at="2026-12-05T20:00:00Z", slots=[{"franchise_ref": "bp:t1"}, {"franchise_ref": "bp:t2"}]),
                      rec("standing", "st27", season_year=2027, franchise_ref="bp:t2", position=1, points=0)])
    everything = " ".join(api.get(path).text for path in (
        "/api/season/current", "/api/events", "/api/matches", "/api/standings", "/api/players", "/api/franchises",
        "/api/championships", "/api/freshness"))
    assert "2027" not in everything
    assert api.get("/api/season/current").json()["year"] == 2026


# --- Plan I-44: los datos nunca salen de la caché del navegador ----------------------------------


def test_las_respuestas_de_la_api_no_se_guardan_en_la_cache(api, clean_db):
    # Safari devolvía una copia guardada de /api/matches y el bloque en vivo no cambiaba (RF-79, RF-82).
    ingest(clean_db, world(maps_won=[3, 0], winner_side=1))
    for path in ("/api/matches", "/api/freshness", "/api/season/current", "/api/players", "/api/admin/me", "/api/health"):
        assert api.get(path).headers["cache-control"] == "no-store", path


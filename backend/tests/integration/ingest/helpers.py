"""Ayudas para escribir registros de fuente en las pruebas de ingesta."""

from datetime import UTC, datetime, timedelta

T0 = datetime(2026, 1, 10, 12, 0, tzinfo=UTC)


def at(hours: float = 0) -> str:
    """Instante de observación relativo a T0, en ISO 8601."""
    return (T0 + timedelta(hours=hours)).isoformat()


def rec(kind: str, source_id: str, source: str = "bp", hours: float = 0, **fields) -> dict:
    """Registro de fuente en bruto."""
    return {"kind": kind, "source": source, "source_id": source_id, "observed_at": at(hours), **fields}


def season_and_event(year: int = 2026, event_id: str = "ev1", source: str = "bp") -> list[dict]:
    return [
        rec("season", f"s{year}", source=source, year=year, name=f"CDL {year}"),
        rec("event", event_id, source=source, season_year=year, name=f"[FICTICIO] Major {year}"),
    ]


def team(source_id: str, name: str, source: str = "bp", hours: float = 0, **identity) -> list[dict]:
    """Franquicia con una identidad."""
    return [
        rec("franchise", source_id, source=source, hours=hours),
        rec("identity", f"{source_id}-id", source=source, hours=hours, franchise_ref=f"{source}:{source_id}",
            short_name=name, **identity),
    ]

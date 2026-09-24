"""Importación de los archivos de la Wiki (spec 003: RF-4 a RF-4c, RF-32, RF-113; plan I-26).

Lee los CSV que prepara Hugo, los pasa por la ingesta de la 002 con la curación vigente (que
respeta uniones, separaciones, retiradas de datos personales y confirmaciones) y lo anota en el
registro de actualizaciones. Todo o nada: si falta un archivo o una columna no se registra
ningún dato, pero el intento fallido sí queda anotado (RF-4b, RF-4c).
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.curation.loader import Curation, CurationError, load_curation
from app.db.models import SourceState, SyncRun
from app.ingest.pipeline import ingest_records
from app.sources.contract import plain_message
from app.sources.wiki_csv import WikiCsvError, read_wiki_csv

SOURCE, JOB = "wiki", "history"
KIND_LABELS = {"championship": "campeonatos", "placement": "clasificaciones", "franchise": "franquicias",
               "player": "jugadores"}


@dataclass
class ImportResult:
    """Resultado de la importación (criterio de RF-105): `success`, `partial` o `failure`."""

    outcome: str
    message: str = ""
    incidents: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)
    retained: list[str] = field(default_factory=list)


def import_wiki_csv(session: Session, directory: Path, curation: Curation | None = None,
                    now: datetime | None = None) -> ImportResult:
    """Importa los archivos de la Wiki de `directory` y confirma la transacción.

    Los registros retenidos (RF-55) no cuentan como fallo: el historial los usa (C-14) y
    `retake list-retained` ayuda a unirlos. Se devuelven aparte.
    """
    now = now or datetime.now(UTC)
    try:
        data = read_wiki_csv(directory, now)
        report = ingest_records(session, data.records, curation=curation if curation is not None else load_curation(),
                                now=now)
    except (WikiCsvError, CurationError) as error:
        session.rollback()
        result = ImportResult("failure", message=f"No se ha importado nada: {error}")
    else:
        incidents = list(data.problems)
        incidents += [f"registro rechazado #{rejection.index}: {rejection.reason}" for rejection in report.rejected]
        incidents += [f"{record['kind']} {record['source_id']}: {name} ilegible"
                      for record in data.records for name in record.get("unreadable", [])]
        counts = {label: sum(record["kind"] == kind for record in data.records) for kind, label in KIND_LABELS.items()}
        outcome = "partial" if incidents else "success"
        summary = ", ".join(f"{label}: {count}" for label, count in counts.items())
        result = ImportResult(outcome, message=f"Importación de la Wiki: {summary}; incidencias: {len(incidents)}.",
                              incidents=incidents, counts=counts, retained=report.retained)
    _log(session, result, now, item_count=sum(result.counts.values()))
    session.commit()
    return result


def _log(session: Session, result: ImportResult, now: datetime, item_count: int) -> None:
    """Anota la importación en el registro y como última importación de la Wiki (RF-4b, RF-113)."""
    session.add(SyncRun(source=SOURCE, job=JOB, started_at=now, finished_at=now, outcome=result.outcome,
                        message=plain_message(result.message)))
    state = session.get(SourceState, (SOURCE, JOB)) or SourceState(source=SOURCE, job=JOB)
    session.add(state)
    state.last_attempt_at = now
    if result.outcome != "failure":
        state.last_success_at = now
        state.last_item_count = item_count
    session.flush()

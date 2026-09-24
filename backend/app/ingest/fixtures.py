"""Carga de los datos de prueba (plan de la spec 002, P-6 y D-16).

- `fixtures/real/`: muestra real transcrita a mano. Cada archivo indica en `consulted`
  la fuente, la dirección y la fecha de consulta, y ningún registro es ficticio.
- `fixtures/fictional/`: registros inventados para cada caso límite. Todos llevan
  `fictional: true` y nombres que empiezan por `[FICTICIO]`.

Los archivos se cargan en orden de nombre (primero la muestra real) para que cada
objeto llegue antes que lo que lo referencia. En producción no se carga nada ficticio.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.orm import Session

from app.curation.loader import FIXTURES_CURATION_PATH, ConfirmedNewEntry, Curation, load_curation
from app.curation.overlay import apply_curation
from app.ingest.pipeline import IngestReport, ingest_records
from app.ingest.retention import RETAINABLE

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"


class FixtureError(ValueError):
    """Los datos de prueba no cumplen sus reglas o no se pueden cargar en este entorno."""


@dataclass
class FixtureFile:
    path: Path
    records: list[dict]
    consulted: list[dict] = field(default_factory=list)

    @property
    def fictional(self) -> bool:
        return self.path.parent.name == "fictional"


@dataclass
class FixtureLoadResult:
    files: list[FixtureFile]
    report: IngestReport


def _read(path: Path) -> FixtureFile:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise FixtureError(f"{path.name}: JSON no válido ({error})") from None
    records = data.get("records")
    if not isinstance(records, list):
        raise FixtureError(f"{path.name}: falta la lista 'records'")
    fixture = FixtureFile(path=path, records=records, consulted=data.get("consulted") or [])
    if fixture.fictional:
        unmarked = [r.get("source_id") for r in records if r.get("fictional") is not True]
        if unmarked:
            raise FixtureError(f"{path.name}: registros sin 'fictional: true' en la carpeta ficticia: {unmarked}")
    else:
        if not fixture.consulted:
            raise FixtureError(f"{path.name}: un archivo de la muestra real debe indicar sus fuentes en 'consulted'")
        marked = [r.get("source_id") for r in records if r.get("fictional")]
        if marked:
            raise FixtureError(f"{path.name}: la muestra real no puede tener registros ficticios: {marked}")
    return fixture


def read_fixture_files(directory: Path = FIXTURES_DIR) -> list[FixtureFile]:
    """Lee y valida todos los archivos de datos de prueba, primero los reales."""
    files = []
    for folder in ("real", "fictional"):
        files += [_read(path) for path in sorted((directory / folder).glob("*.json"))]
    return files


def confirm_real_sample(curation: Curation, files: list[FixtureFile]) -> Curation:
    """Confirma como nueva la muestra real (spec 003, RF-56; registro I-20 del plan de la 003).

    La muestra real de la 002 se transcribió de la Wiki y, en los datos de prueba, BreakingPoint
    no publica esos mismos objetos. Sin esta confirmación quedaría retenida (RF-55) y la demo
    se vería vacía. Solo vale para los datos de prueba: el archivo de curación no se toca.
    """
    extra = [
        ConfirmedNewEntry(kind=record["kind"], ref=f"{record['source']}:{record['source_id']}",
                          reason="Muestra real de los datos de prueba")
        for fixture in files if not fixture.fictional
        for record in fixture.records if record["kind"] in RETAINABLE
    ]
    return curation.model_copy(update={"confirmed_new": [*curation.confirmed_new, *extra]})


def load_fixtures(
    session: Session, app_env: str, directory: Path = FIXTURES_DIR, curation: Curation | None = None
) -> FixtureLoadResult:
    """Carga los datos de prueba y aplica la curación. Quien llama confirma la transacción.

    Raises:
        FixtureError: si algún archivo no es válido o se intenta cargar datos ficticios en producción.
    """
    files = read_fixture_files(directory)
    if app_env == "production" and any(f.fictional for f in files):
        raise FixtureError("No se cargan datos ficticios en producción (APP_ENV=production).")
    curation = confirm_real_sample(curation if curation is not None else load_curation(FIXTURES_CURATION_PATH), files)
    report = ingest_records(session, [record for f in files for record in f.records], curation=curation)
    apply_curation(session, curation)
    return FixtureLoadResult(files=files, report=report)

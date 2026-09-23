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

from app.curation.loader import Curation, load_curation
from app.curation.overlay import apply_curation
from app.ingest.pipeline import IngestReport, ingest_records

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
    curation = curation if curation is not None else load_curation()
    report = ingest_records(session, [record for f in files for record in f.records], curation=curation)
    apply_curation(session, curation)
    return FixtureLoadResult(files=files, report=report)

"""Comandos de línea de Retake (plan de la spec 002, §1).

Uso: `uv run retake <comando>`.
"""

import argparse
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

BACKEND_DIR = Path(__file__).resolve().parent.parent


def migrate() -> None:
    """Aplica todas las migraciones pendientes sobre la base de datos de `DATABASE_URL`."""
    command.upgrade(Config(str(BACKEND_DIR / "alembic.ini")), "head")
    print("Migraciones aplicadas.")


def apply_curation_command() -> None:
    """Aplica `curation/curation.yaml` a la base de datos de `DATABASE_URL`, entero o nada."""
    from sqlalchemy.orm import Session

    from app.curation.loader import CURATION_PATH, CurationError, load_curation
    from app.curation.overlay import apply_curation
    from app.db.engine import get_engine

    try:
        curation = load_curation()
        with Session(get_engine()) as session:
            apply_curation(session, curation)
            session.commit()
    except CurationError as error:
        print(f"No se ha aplicado la curación: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    print(
        f"Curación aplicada desde {CURATION_PATH}: {len(curation.roles)} roles, "
        f"{len(curation.player_merges)} uniones, {len(curation.player_splits)} separaciones, "
        f"{len(curation.personal_data_removals)} retiradas."
    )


def load_fixtures_command() -> None:
    """Carga los datos de prueba en la base de datos de `DATABASE_URL` y aplica la curación."""
    from sqlalchemy.orm import Session

    from app.config import get_settings
    from app.curation.loader import CurationError
    from app.db.engine import get_engine
    from app.ingest.fixtures import FixtureError, load_fixtures

    try:
        with Session(get_engine()) as session:
            result = load_fixtures(session, app_env=get_settings().app_env)
            session.commit()
    except (FixtureError, CurationError) as error:
        print(f"No se han cargado los datos de prueba: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    report = result.report
    print(f"Archivos: {len(result.files)} · registros aceptados: {report.accepted} · rechazados: {len(report.rejected)}")
    for rejection in report.rejected:
        print(f"  rechazado #{rejection.index}: {rejection.reason}", file=sys.stderr)
    if report.rejected:
        raise SystemExit(1)


COMMANDS = {
    "migrate": (migrate, "Aplica las migraciones pendientes a la base de datos."),
    "load-fixtures": (load_fixtures_command, "Carga los datos de prueba (muestra real y ficticios) y aplica la curación."),
    "apply-curation": (apply_curation_command, "Aplica el archivo de curación (roles, uniones, separaciones, retiradas)."),
}


def main(argv: list[str] | None = None) -> None:
    """Punto de entrada del comando `retake`."""
    parser = argparse.ArgumentParser(prog="retake", description="Comandos del backend de Retake.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, (_, help_text) in COMMANDS.items():
        subparsers.add_parser(name, help=help_text)
    args = parser.parse_args(argv)
    COMMANDS[args.command][0]()

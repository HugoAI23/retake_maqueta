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
        f"{len(curation.personal_data_removals)} retiradas, {len(curation.merges)} uniones de partidos, eventos "
        f"o franquicias, {len(curation.confirmed_new)} confirmados como nuevos, {len(curation.countries)} países."
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


def import_wiki_csv_command(directory: str | None = None) -> None:
    """Importa los archivos CSV de la Wiki (spec 003, RF-4 a RF-4c; plan I-26)."""
    from sqlalchemy.orm import Session

    from app.config import get_settings
    from app.db import engine
    from app.ingest.wiki_import import import_wiki_csv

    folder = Path(directory) if directory else get_settings().wiki_csv_dir
    with Session(engine.get_engine()) as session:
        result = import_wiki_csv(session, folder)
    if result.outcome == "failure":
        print(result.message, file=sys.stderr)
        raise SystemExit(1)
    print(f"Resultado: {result.outcome} · carpeta: {folder}")
    print(" · ".join(f"{label}: {count}" for label, count in result.counts.items()))
    print(f"Incidencias: {len(result.incidents)}")
    for incident in result.incidents:
        print(f"  - {incident}")
    if result.retained:
        print(f"Registros retenidos nuevos: {len(result.retained)} (revísalos con `uv run retake list-retained`).")


KIND_NAMES = {"match": "partido", "event": "evento", "franchise": "franquicia", "player": "jugador"}


def list_retained_command() -> None:
    """Lista los registros retenidos y sugiere candidatos parecidos; nunca une nada (spec 003, T-047)."""
    from sqlalchemy.orm import Session

    from app.curation.retained import list_retained
    from app.db import engine

    with Session(engine.get_engine()) as session:
        items = list_retained(session)
        session.rollback()  # solo lectura
    print(f"Registros retenidos: {len(items)}. Solo son sugerencias: esta orden nunca une nada.")
    for item in items:
        print(f"- {KIND_NAMES[item.kind]} {item.ref} «{item.label}» · retenido desde {item.since:%Y-%m-%d %H:%M} UTC")
        for candidate in item.candidates:
            print(f"    candidato: {candidate.ref} «{candidate.label}»")
    if items:
        print("Para unir, añade una entrada a `merges` (o a `player_merges`) en curation.yaml; si es nuevo, "
              "a `confirmed_new`. Después, `uv run retake apply-curation`.")


def sync_once_command(source: str) -> None:
    """Realiza una consulta a BreakingPoint y muestra el resultado sin guardar en la BD.

    La Wiki no se consulta (spec 003, C-18): se importa con `retake import-wiki-csv`.
    """
    from datetime import UTC, datetime

    from app.sources.bp import consult_regular
    from app.sources.http import real_client

    client = real_client(source)
    print("Consultando BreakingPoint.gg (temporadas, eventos, partidos)...")
    result = consult_regular(client, datetime.now(UTC))

    print(f"Resultado: {result.outcome} · Registros: {len(result.records)} · Vistos: {len(result.seen)} · Rechazados: {len(result.rejected)}")
    if result.message:
        print(f"Mensaje: {result.message}")
    if result.rejected:
        for rej in result.rejected[:5]:
            print(f"  Rechazado: {rej.ref} [{rej.field}]: {rej.reason}")
    if result.records:
        kinds: dict[str, int] = {}
        for r in result.records:
            kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
        print("Desglose por tipo:", ", ".join(f"{k}: {v}" for k, v in kinds.items()))
        print(f"Primer registro ({result.records[0]['kind']}):", result.records[0])


COMMANDS = {
    "migrate": (migrate, "Aplica las migraciones pendientes a la base de datos."),
    "load-fixtures": (load_fixtures_command, "Carga los datos de prueba (muestra real y ficticios) y aplica la curación."),
    "apply-curation": (apply_curation_command, "Aplica el archivo de curación (roles, uniones, separaciones, retiradas)."),
    "sync-once": (sync_once_command, "Consulta BreakingPoint y muestra lo que devuelve, sin guardar nada."),
    "list-retained": (list_retained_command, "Lista los registros retenidos y sugiere candidatos (nunca une nada)."),
    "import-wiki-csv": (import_wiki_csv_command, "Importa los archivos CSV de la Wiki (historial y datos personales)."),
}


def main(argv: list[str] | None = None) -> None:
    """Punto de entrada del comando `retake`."""
    parser = argparse.ArgumentParser(prog="retake", description="Comandos del backend de Retake.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, (_, help_text) in COMMANDS.items():
        sub = subparsers.add_parser(name, help=help_text)
        if name == "import-wiki-csv":
            sub.add_argument("--dir", help="Carpeta con los CSV (por defecto WIKI_CSV_DIR, backend/data/wiki/).")
        if name == "sync-once":
            sub.add_argument("--source", choices=["bp"], required=True, help="Fuente a consultar (solo bp).")
    args = parser.parse_args(argv)
    fn = COMMANDS[args.command][0]
    if args.command == "sync-once":
        fn(source=args.source)
    elif args.command == "import-wiki-csv":
        fn(directory=args.dir)
    else:
        fn()

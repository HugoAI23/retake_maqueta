"""Comandos de línea de Retake (plan de la spec 002, §1).

Uso: `uv run retake <comando>`.
"""

import argparse
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parent.parent


def migrate() -> None:
    """Aplica todas las migraciones pendientes sobre la base de datos de `DATABASE_URL`."""
    command.upgrade(Config(str(BACKEND_DIR / "alembic.ini")), "head")
    print("Migraciones aplicadas.")


def apply_curation_command() -> None:
    """Aplica la curación del modo de fuente a la base de datos de `DATABASE_URL`, entero o nada (plan I-35)."""
    from sqlalchemy.orm import Session

    from app.config import get_settings
    from app.curation import loader
    from app.curation.loader import CurationError
    from app.curation.overlay import apply_curation
    from app.db.engine import get_engine

    path = loader.curation_path(get_settings().source_mode)
    try:
        curation = loader.load_curation(path)
        with Session(get_engine()) as session:
            apply_curation(session, curation)
            session.commit()
    except CurationError as error:
        print(f"No se ha aplicado la curación: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    print(
        f"Curación aplicada desde {path}: {len(curation.roles)} roles, "
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
    from app.curation.loader import curation_path, load_curation
    from app.db import engine
    from app.ingest.wiki_import import import_wiki_csv

    settings = get_settings()
    folder = Path(directory) if directory else settings.wiki_csv_dir
    with Session(engine.get_engine()) as session:
        # La curación del modo de fuente (I-35): la Wiki también se importa sobre los datos de prueba.
        result = import_wiki_csv(session, folder, curation=load_curation(curation_path(settings.source_mode)))
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


def set_admin_password_command() -> None:
    """Crea o cambia la cuenta del administrador (spec 003: RF-121 a RF-123; plan D-12).

    Pide la contraseña sin mostrarla y dos veces; nunca la recibe como argumento, así que no
    queda en el historial de la terminal. Al cambiarla se cierran todas las sesiones abiertas.
    """
    import getpass
    from datetime import UTC, datetime

    from sqlalchemy.orm import Session

    from app.admin.accounts import set_admin_password
    from app.db import engine

    username = input("Usuario del administrador: ").strip()
    password = getpass.getpass("Contraseña (no se muestra): ")
    if password != getpass.getpass("Repite la contraseña: "):
        print("Las contraseñas no coinciden. No se ha cambiado nada.", file=sys.stderr)
        raise SystemExit(1)
    try:
        with Session(engine.get_engine()) as session:
            set_admin_password(session, username, password, datetime.now(UTC))
            session.commit()
    except ValueError as error:
        print(f"No se ha cambiado nada: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    print(f"Cuenta del administrador «{username}» guardada. Las sesiones abiertas se han cerrado.")


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


def sync_command() -> None:
    """Arranca el trabajador continuo de sincronización periódica (spec 003, §3.4, T-053)."""
    from app.sync.worker import SyncWorker

    try:
        SyncWorker().run()
    except KeyboardInterrupt:
        print("\n[retake sync] Detenido por el usuario.")
    except RuntimeError as error:  # modo fixtures, datos ficticios en producción (RF-9 a RF-11) u otro proceso en marcha (I-34)
        print(f"No se ha arrancado la obtención: {error}", file=sys.stderr)
        raise SystemExit(1) from None


def set_source_mode(
    session: Session,
    mode: str,
    app_env: str,
    env_file: Path | None = None,
) -> None:
    """Cambia el modo de fuentes en desarrollo, borra la liga y programa carga inicial (RF-11 a RF-13).

    Args:
        session: Sesión de SQLAlchemy activa.
        mode: Uno de 'fixtures', 'real', 'simulated'.
        app_env: Entorno de ejecución ('development', 'production', 'test').
        env_file: Ruta del archivo .env a actualizar (por defecto backend/.env).
    """
    if app_env != "development":
        print(
            f"El comando source-mode solo está permitido en el entorno de desarrollo (entorno actual: {app_env}) (RF-11 a RF-13).",
            file=sys.stderr,
        )
        raise SystemExit(1)

    if mode not in ("fixtures", "real", "simulated"):
        print(f"Modo no válido: {mode!r}. Debe ser fixtures, real o simulated.", file=sys.stderr)
        raise SystemExit(1)

    # 1. Borrar datos de la liga (RF-12)
    from sqlalchemy import delete
    from app.db.models import (
        Championship,
        DailySummary,
        DatasetChange,
        Event,
        ExternalRef,
        Franchise,
        Identity,
        Incident,
        LogoImage,
        Match,
        Observation,
        Player,
        RefLink,
        Season,
        SourceState,
        SyncJob,
        SyncRun,
    )

    session.execute(delete(Observation))
    session.execute(delete(RefLink))
    session.execute(delete(ExternalRef))
    session.execute(delete(DatasetChange))
    session.execute(delete(SourceState))
    session.execute(delete(SyncJob))
    session.execute(delete(Championship))
    session.execute(delete(Match))
    session.execute(delete(Player))
    session.execute(delete(Identity))
    session.execute(delete(Franchise))
    session.execute(delete(Event))
    session.execute(delete(Season))
    session.execute(delete(LogoImage))
    # El registro, las incidencias y los resúmenes eran del modo anterior (RF-12; cambio C-27).
    # La cuenta de administración, sus sesiones y el bloqueo por intentos fallidos se conservan.
    session.execute(delete(SyncRun))
    session.execute(delete(Incident))
    session.execute(delete(DailySummary))
    session.flush()

    # 2. Carga inicial según el modo elegido (RF-13)
    if mode == "fixtures":
        from app.ingest.fixtures import load_fixtures

        load_fixtures(session, app_env=app_env)
    else:
        from datetime import UTC, datetime

        now = datetime.now(UTC)
        session.add(
            SyncJob(
                key=f"initial_load_{int(now.timestamp())}",
                kind="initial_load",
                due_at=now,
            )
        )
    session.flush()

    # 3. Actualizar SOURCE_MODE en .env
    target_env = env_file if env_file is not None else (BACKEND_DIR / ".env")
    if target_env.exists():
        content = target_env.read_text(encoding="utf-8")
        lines = content.splitlines()
        found = False
        new_lines = []
        for line in lines:
            if line.startswith("SOURCE_MODE="):
                new_lines.append(f"SOURCE_MODE={mode}")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"SOURCE_MODE={mode}")
        target_env.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def source_mode_command(mode: str) -> None:
    """Comando CLI para cambiar el modo de fuentes (RF-11 a RF-13)."""
    from sqlalchemy.orm import Session
    from app.config import get_settings
    from app.db.engine import get_engine

    settings = get_settings()
    with Session(get_engine()) as session:
        set_source_mode(session, mode=mode, app_env=settings.app_env)
        session.commit()
    print(f"Modo cambiado a '{mode}'. Datos de la liga y registro del modo anterior borrados; carga inicial preparada.")
    print("El historial de la Wiki también se ha borrado: vuelve a importarlo con `uv run retake import-wiki-csv`.")


COMMANDS = {
    "migrate": (migrate, "Aplica las migraciones pendientes a la base de datos."),
    "load-fixtures": (load_fixtures_command, "Carga los datos de prueba (muestra real y ficticios) y aplica la curación."),
    "apply-curation": (apply_curation_command, "Aplica el archivo de curación (roles, uniones, separaciones, retiradas)."),
    "sync": (sync_command, "Arranca el trabajador continuo de sincronización periódica."),
    "sync-once": (sync_once_command, "Consulta BreakingPoint y muestra lo que devuelve, sin guardar nada."),
    "source-mode": (source_mode_command, "Cambia el modo de fuentes en desarrollo, borra la liga y programa carga inicial."),
    "list-retained": (list_retained_command, "Lista los registros retenidos y sugiere candidatos (nunca une nada)."),
    "import-wiki-csv": (import_wiki_csv_command, "Importa los archivos CSV de la Wiki (historial y datos personales)."),
    "set-admin-password": (set_admin_password_command, "Crea o cambia la cuenta del administrador (pide la contraseña sin mostrarla)."),
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
        if name == "source-mode":
            sub.add_argument("mode", choices=["fixtures", "real", "simulated"], help="Modo de fuentes a activar.")
    args = parser.parse_args(argv)
    fn = COMMANDS[args.command][0]
    if args.command == "sync-once":
        fn(source=args.source)
    elif args.command == "import-wiki-csv":
        fn(directory=args.dir)
    elif args.command == "source-mode":
        fn(mode=args.mode)
    else:
        fn()

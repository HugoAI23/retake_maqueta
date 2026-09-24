"""Importación de los archivos CSV de la Wiki (spec 003: RF-4 a RF-4c, RF-32; plan I-26).

Retake no consulta la Wiki (RF-38). Hugo prepara los CSV fuera de Retake, con el formato de
`CDL-data-analysis`, y los actualiza tras cada Champs. Este módulo solo los lee y los convierte
en registros de fuente `wiki`, que después pasan por la ingesta de la 002 como los de cualquier
otra fuente.

- `cdl_all_years_champs_prizepool.csv` (obligatorio): una fila por jugador de cada equipo
  clasificado en cada campeonato. Se agrupa en una clasificación por año y equipo, con su
  roster: el premio es del equipo, nunca de cada jugador (RF-7 de la 002).
- `players_birthday.csv` (obligatorio): nombre real y fecha de nacimiento por gamertag.
- `cdl_<año>_rosters.csv` (opcionales): país, nombre y fecha de nacimiento. Las redes sociales
  y la edad nunca se leen.

Solo se registran datos personales de los jugadores que figuran en el historial o en un roster
(RF-4a). Los equipos y los jugadores se identifican por su nombre, porque los CSV no traen el
identificador de su página en la Wiki.
"""

import csv
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

SOURCE = "wiki"
HISTORY_FILE = "cdl_all_years_champs_prizepool.csv"
BIRTHDAYS_FILE = "players_birthday.csv"
ROSTERS_PATTERN = "cdl_*_rosters.csv"

HISTORY_COLUMNS = ("Place", "Year", "Game Version", "final_date", "Prize", "Prize (%)", "Team", "Player")
BIRTHDAYS_COLUMNS = ("Player", "Name", "Birthday")
ROSTERS_COLUMNS = ("ID", "Country", "Name", "Birthday")

# Tabla de referencia de los campeonatos mundiales (RF-54 y RF-58 de la 002), mantenida a mano
# como en `CDL-data-analysis`: nombre oficial y abreviatura del juego de cada año. Un año que no
# esté aquí usa el nombre del CSV, sin abreviatura, hasta añadirlo.
GAMES = {
    2013: ("Call of Duty: Black Ops II", "BO2"),
    2014: ("Call of Duty: Ghosts", "Ghosts"),
    2015: ("Call of Duty: Advanced Warfare", "AW"),
    2016: ("Call of Duty: Black Ops III", "BO3"),
    2017: ("Call of Duty: Infinite Warfare", "IW"),
    2018: ("Call of Duty: WWII", "WWII"),
    2019: ("Call of Duty: Black Ops 4", "BO4"),
    2020: ("Call of Duty: Modern Warfare", "MW"),
    2021: ("Call of Duty: Black Ops Cold War", "CW"),
    2022: ("Call of Duty: Vanguard", "VG"),
    2023: ("Call of Duty: Modern Warfare II", "MWII"),
    2024: ("Call of Duty: Modern Warfare III", "MWIII"),
    2025: ("Call of Duty: Black Ops 6", "BO6"),
    2026: ("Call of Duty: Black Ops 7", "BO7"),
}

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_NUMBER = re.compile(r"^-?\d+(?:\.\d+)?$")


class WikiCsvError(ValueError):
    """Falta un archivo o una columna: no se importa nada (RF-4c)."""


@dataclass
class WikiCsvData:
    """Registros de fuente listos para la ingesta y problemas de filas sueltas (importación parcial)."""

    records: list[dict] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)


def competition(year: int) -> str:
    """Nombre del campeonato mundial de ese año (RF-54 de la 002)."""
    if year <= 2015:
        return "Call of Duty Championship"
    if year <= 2019:
        return "Call of Duty World League Championship"
    return "Call of Duty League Championship"


def championship_page(year: int) -> str:
    """Identificador del campeonato: el nombre de su página en la Wiki."""
    return f"{competition(year).replace(' ', '_')}_{year}"


def _id(name: str) -> str:
    """Nombre de equipo o gamertag como identificador: espacios → guiones bajos."""
    return name.strip().replace(" ", "_")


def _ref(source_id: str) -> str:
    return f"{SOURCE}:{source_id}"


def _record(kind: str, source_id: str, observed_at: datetime, **fields) -> dict:
    record = {"kind": kind, "source": SOURCE, "source_id": source_id, "observed_at": observed_at.isoformat()}
    record.update({name: value for name, value in fields.items() if value is not None and value != []})
    return record


def _number(text: str) -> tuple[object, bool]:
    """`$ 800,000` → 800000; `40%` → 40. Devuelve `(valor, legible)`; vacío o `-` = no publicado."""
    raw = (text or "").replace("$", "").replace("%", "").replace(",", "").strip()
    if raw in ("", "-", "—", "–"):
        return None, True
    if not _NUMBER.match(raw):
        return None, False
    value = float(raw)
    return (int(value) if value.is_integer() else value), True


def _date(text: str) -> tuple[str | None, bool]:
    raw = (text or "").strip()
    if not raw:
        return None, True
    return (raw, True) if _DATE.match(raw) else (None, False)


def _read(path: Path, columns: tuple[str, ...]) -> list[dict]:
    """Filas de un CSV con las columnas indicadas (acepta la marca BOM de Excel).

    Raises:
        WikiCsvError: si falta alguna columna.
    """
    with open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = sorted(set(columns) - set(reader.fieldnames or []))
        if missing:
            raise WikiCsvError(f"{path.name}: faltan las columnas {', '.join(missing)}")
        return [{name: (row.get(name) or "").strip() for name in columns} for row in reader]


def _require(directory: Path, name: str) -> Path:
    path = directory / name
    if not path.is_file():
        raise WikiCsvError(f"falta el archivo {name} en {directory}")
    return path


def read_wiki_csv(directory: Path, observed_at: datetime) -> WikiCsvData:
    """Lee los archivos de la Wiki y los convierte en registros de fuente.

    Raises:
        WikiCsvError: si la carpeta no existe, o falta un archivo obligatorio o una columna (RF-4c).
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise WikiCsvError(f"la carpeta de los archivos de la Wiki no existe: {directory}")
    history = _read(_require(directory, HISTORY_FILE), HISTORY_COLUMNS)
    birthdays = _read(_require(directory, BIRTHDAYS_FILE), BIRTHDAYS_COLUMNS)
    rosters = [(path.name, _read(path, ROSTERS_COLUMNS)) for path in sorted(directory.glob(ROSTERS_PATTERN))]

    data = WikiCsvData()
    championships: dict[int, dict] = {}
    teams: dict[tuple[int, str], dict] = {}
    for number, row in enumerate(history, start=2):  # la fila 1 es la cabecera
        try:
            year = int(row["Year"])
        except ValueError:
            data.problems.append(f"{HISTORY_FILE}, fila {number}: año no válido: {row['Year']!r}")
            continue
        team, player = row["Team"], row["Player"]
        if not team or not player:
            data.problems.append(f"{HISTORY_FILE}, fila {number}: falta el equipo o el jugador")
            continue
        championships.setdefault(year, {"version": row["Game Version"], "final": row["final_date"], "places": []})
        entry = teams.setdefault((year, team), {"row": row, "players": []})
        if player not in entry["players"]:
            entry["players"].append(player)
        championships[year]["places"].append(row["Place"])

    # Datos personales: el roster de temporada manda sobre el archivo de fechas de nacimiento.
    personal: dict[str, dict] = {}
    for row in birthdays:
        if row["Player"]:
            personal.setdefault(row["Player"].casefold(), {}).update(real_name=row["Name"], birth=row["Birthday"])
    roster_players: list[str] = []
    for _, rows in rosters:
        for row in rows:
            if not row["ID"]:
                continue
            roster_players.append(row["ID"])
            info = personal.setdefault(row["ID"].casefold(), {})
            info.update({k: v for k, v in (("real_name", row["Name"]), ("birth", row["Birthday"]),
                                           ("country", row["Country"])) if v})

    for year, info in sorted(championships.items()):
        name, abbreviation = GAMES.get(year, (f"Call of Duty: {info['version']}" if info["version"] else None, None))
        final, final_ok = _date(info["final"])
        data.records.append(_record(
            "championship", championship_page(year), observed_at, year=year, competition=competition(year),
            game_name=name, game_abbreviation=abbreviation, final_date=final,
            completed=True if "1" in info["places"] else None,
            unreadable=[] if final_ok else ["final_date"],
        ))
    for team in dict.fromkeys(team for _, team in teams):
        data.records.append(_record("franchise", _id(team), observed_at))
        data.records.append(_record("identity", f"{_id(team)}#identity", observed_at,
                                    franchise_ref=_ref(_id(team)), short_name=team))

    gamertags = dict.fromkeys([p for entry in teams.values() for p in entry["players"]] + roster_players)
    for gamertag in gamertags:
        info = personal.get(gamertag.casefold(), {})
        birth, birth_ok = _date(info.get("birth", ""))
        data.records.append(_record(
            "player", _id(gamertag), observed_at, gamertag=gamertag,
            real_name=info.get("real_name") or None, country=info.get("country") or None, birth_date=birth,
            unreadable=[] if birth_ok else ["birth_date"],
        ))

    for (year, team), entry in teams.items():
        row = entry["row"]
        prize, prize_ok = _number(row["Prize"])
        percent, percent_ok = _number(row["Prize (%)"])
        data.records.append(_record(
            "placement", f"{championship_page(year)}/{_id(team)}", observed_at,
            championship_ref=_ref(championship_page(year)), franchise_ref=_ref(_id(team)),
            published_team_name=team, place=row["Place"] or None, prize_usd=prize, pool_percent=percent,
            roster=[{"player_ref": _ref(_id(p)), "gamertag_at_final": p} for p in entry["players"]],
            unreadable=[name for name, ok in (("prize_usd", prize_ok), ("pool_percent", percent_ok)) if not ok],
        ))
    return data

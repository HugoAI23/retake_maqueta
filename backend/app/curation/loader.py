"""Lectura y validación del archivo de curación (plan de la spec 002, §2.2 y P-4).

El archivo solo contiene referencias externas y motivos, nunca datos personales (plan §5).
Si tiene un error de formato, no se aplica nada.
"""

from datetime import date
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.ingest.records import RefKey

# Archivo de curación del proyecto, versionado en git.
CURATION_PATH = Path(__file__).resolve().parent.parent.parent / "curation" / "curation.yaml"


class CurationError(ValueError):
    """El archivo de curación no es válido o contradice los datos; no se aplica nada."""


class _Entry(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RoleEntry(_Entry):
    """Rol que Retake asigna a un jugador (RF-26)."""

    player: RefKey
    role: Literal["SMG", "AR"]
    reason: str = Field(min_length=1)


class MergeEntry(_Entry):
    """Referencias que son la misma persona (RF-131)."""

    players: list[RefKey] = Field(min_length=2)
    reason: str = Field(min_length=1)


class SplitEntry(_Entry):
    """Dos referencias que una fuente relaciona pero son personas distintas (RF-133)."""

    players: tuple[RefKey, RefKey]
    reason: str = Field(min_length=1)


class RemovalEntry(_Entry):
    """Petición de retirada de los datos personales de un jugador (RF-78)."""

    player: RefKey
    requested_on: date


class Curation(_Entry):
    """Contenido completo del archivo de curación."""

    roles: list[RoleEntry] = Field(default_factory=list)
    player_merges: list[MergeEntry] = Field(default_factory=list)
    player_splits: list[SplitEntry] = Field(default_factory=list)
    personal_data_removals: list[RemovalEntry] = Field(default_factory=list)


def parse_curation(text: str) -> Curation:
    """Lee el contenido YAML de un archivo de curación.

    Raises:
        CurationError: si el YAML está roto o no tiene la forma esperada.
    """
    try:
        data = yaml.safe_load(text) or {}
    except yaml.YAMLError as error:
        raise CurationError(f"El archivo de curación no es YAML válido: {error}") from None
    try:
        return Curation.model_validate(data)
    except ValidationError as error:
        problems = "; ".join(
            f"{'.'.join(str(part) for part in issue['loc'])}: {issue['msg']}" for issue in error.errors()
        )
        raise CurationError(f"El archivo de curación no es válido: {problems}") from None


def load_curation(path: Path = CURATION_PATH) -> Curation:
    """Lee el archivo de curación; si no existe, devuelve una curación vacía."""
    if not path.exists():
        return Curation()
    return parse_curation(path.read_text(encoding="utf-8"))

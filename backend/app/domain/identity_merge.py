"""Identidad combinada campo a campo entre fuentes (spec 003: RF-61 a RF-63).

Sustituye el comportamiento del ajuste I-15 de la 002, que guardaba una identidad por
fuente: ahora hay una sola identidad vigente, y cada campo sale de la fuente con más
prioridad que lo publica. Solo nace una identidad nueva si cambia el resultado combinado.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from app.domain.identities import IdentityData, needs_new_identity
from app.domain.priority import SourceValue, resolve

DATA_FIELDS = ("short_name", "abbreviation", "logo_url", "primary_color", "secondary_color")


@dataclass(frozen=True)
class SourceIdentity:
    """Identidad de una franquicia tal como la publica una fuente.

    `invalid_fields` son los campos que la validación descartó (p. ej. un logo que no es
    una imagen `https`): no cuentan al combinar.
    """

    source: str
    short_name: str | None = None
    abbreviation: str | None = None
    logo_url: str | None = None
    primary_color: str | None = None
    secondary_color: str | None = None
    valid_from: datetime | None = None
    invalid_fields: frozenset[str] | set[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class MergedIdentity:
    """Resultado de combinar las identidades de todas las fuentes."""

    data: IdentityData
    valid_from: datetime | None


def _field(identities: list[SourceIdentity], name: str) -> object:
    return resolve(
        SourceValue(identity.source, getattr(identity, name), is_valid=name not in identity.invalid_fields)
        for identity in identities
    )


def merge_identities(identities: Iterable[SourceIdentity]) -> MergedIdentity | None:
    """Combina campo a campo, incluida la fecha de vigencia (RF-62, decisión Q-45).

    Returns:
        La identidad combinada, o `None` si ninguna fuente publica identidad.
    """
    identities = list(identities)
    if not identities:
        return None
    data = IdentityData(*(_field(identities, name) for name in DATA_FIELDS))
    return MergedIdentity(data=data, valid_from=_field(identities, "valid_from"))


def identity_changed(previous: IdentityData | None, merged: IdentityData) -> bool:
    """Nace una identidad nueva solo si cambia el resultado combinado (RF-63, RF-73 de la 002).

    La fecha de vigencia no forma parte de la comparación: es la fecha de la identidad, no uno
    de sus cinco datos.
    """
    return needs_new_identity(previous, merged)

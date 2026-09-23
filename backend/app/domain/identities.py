"""Identidades de una franquicia (RF-11 a RF-13, RF-73, RF-74, RF-121, RF-124; plan §3.6)."""

from collections.abc import Sequence
from datetime import UTC, date, datetime, time
from typing import NamedTuple


class IdentityData(NamedTuple):
    """Los cinco datos de una identidad (RF-11)."""

    short_name: str
    abbreviation: str | None
    logo_url: str | None
    primary_color: str | None
    secondary_color: str | None


class IdentityVersion(NamedTuple):
    """Una identidad con su identificador y el instante desde el que está vigente (RF-74)."""

    id: object
    data: IdentityData
    valid_from: datetime


def needs_new_identity(latest: IdentityData | None, incoming: IdentityData) -> bool:
    """Nace una identidad nueva si cambia cualquiera de los cinco datos (RF-73)."""
    return latest is None or tuple(latest) != tuple(incoming)


def identity_valid_from(published: datetime | None, observed_at: datetime) -> datetime:
    """Vigencia de una identidad nueva: la fecha que publica la fuente o, si no hay, la de observación."""
    return published if published is not None else observed_at


def identity_at(identities: Sequence[IdentityVersion], instant: datetime) -> IdentityVersion | None:
    """Identidad vigente en un instante: la última con `valid_from` ≤ instante (RF-12, RF-13).

    Si el instante es anterior a todas las identidades conocidas, se usa la primera:
    es la identidad más antigua que se conoce de la franquicia.
    """
    if not identities:
        return None
    ordered = sorted(identities, key=lambda identity: identity.valid_from)
    current = ordered[0]
    for identity in ordered:
        if identity.valid_from <= instant:
            current = identity
    return current


def _end_of_day(day: date) -> datetime:
    return datetime.combine(day, time.max, tzinfo=UTC)


def _normalize_name(name: str) -> str:
    return name.strip().casefold()


def identity_for_championship(
    identities: Sequence[IdentityVersion],
    final_date: date | None,
    published_team_name: str | None,
    year: int,
) -> IdentityVersion | None:
    """Identidad de un equipo en un campeonato del historial.

    1. Con fecha de final: la vigente al terminar ese día, porque un cambio el mismo
       día de la final ya estaba en vigor cuando se jugó (RF-13).
    2. Sin fecha: la identidad cuyo nombre corto coincide con el nombre publicado para
       ese equipo en ese campeonato, sin distinguir mayúsculas ni espacios exteriores (RF-121).
    3. Sin coincidencia: la vigente el 31 de diciembre de ese año (RF-124).
    """
    if final_date is not None:
        return identity_at(identities, _end_of_day(final_date))

    end_of_year = _end_of_day(date(year, 12, 31))
    if published_team_name:
        wanted = _normalize_name(published_team_name)
        matches = [i for i in identities if _normalize_name(i.data.short_name) == wanted]
        if matches:
            # Si el mismo nombre se usó más de una vez, la última vigente ese año.
            return identity_at(matches, end_of_year)

    return identity_at(identities, end_of_year)

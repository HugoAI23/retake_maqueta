"""Base declarativa de los modelos de SQLAlchemy.

Todos los modelos de las tablas del plan §3 heredan de `Base`; Alembic lee
`Base.metadata` para generar las migraciones. La convención de nombres da a cada
restricción un nombre estable, para que las migraciones futuras puedan referirse a ellas.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Clase base de todos los modelos de la base de datos."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

"""Correcciones de datos ya registrados (RF-96 a RF-98; plan D-9)."""


def is_correction(
    *, entity_closed: bool, had_previous_observation: bool, old_value: object, new_value: object
) -> bool:
    """Decide si un cambio del valor resuelto es una corrección.

    Args:
        entity_closed: La entidad está cerrada: partido `finished` (o uno de sus mapas y
            estadísticas) o registro del historial de campeonatos (RF-96).
        had_previous_observation: El campo ya había recibido alguna observación, válida o
            no. La primera llegada de un dato no es una corrección (RF-98).
        old_value: Valor resuelto antes del cambio.
        new_value: Valor resuelto después del cambio.
    """
    return entity_closed and had_previous_observation and old_value != new_value


def add_corrected_field(corrected_fields: list[str], field: str) -> list[str]:
    """Añade un campo a la lista de corregidos sin duplicarlo (RF-97)."""
    return corrected_fields if field in corrected_fields else [*corrected_fields, field]

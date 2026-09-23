"""T-026 · Correcciones (RF-96 a RF-98)."""

from app.domain.corrections import add_corrected_field, is_correction


def test_partido_finalizado_con_un_valor_que_cambia_es_una_correccion():
    assert is_correction(entity_closed=True, had_previous_observation=True, old_value=3, new_value=2)


def test_partido_en_vivo_que_cambia_no_es_una_correccion():
    assert not is_correction(entity_closed=False, had_previous_observation=True, old_value=1, new_value=2)


def test_la_primera_llegada_de_un_dato_no_es_una_correccion():
    assert not is_correction(entity_closed=True, had_previous_observation=False, old_value=None, new_value=25)


def test_dato_no_valido_y_luego_valido_en_partido_finalizado_es_una_correccion():
    # El valor resuelto era nulo (el no válido se descartó), pero el dato ya había llegado.
    assert is_correction(entity_closed=True, had_previous_observation=True, old_value=None, new_value=25)


def test_mismo_valor_no_es_una_correccion():
    assert not is_correction(entity_closed=True, had_previous_observation=True, old_value=3, new_value=3)


def test_marcar_un_campo_no_lo_duplica():
    assert add_corrected_field(["kills"], "kills") == ["kills"]
    assert add_corrected_field(["kills"], "deaths") == ["kills", "deaths"]

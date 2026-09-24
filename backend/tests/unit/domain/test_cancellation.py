"""T-018 · Cancelación según la prioridad de fuentes (RF-53)."""

from app.domain.cancellation import CANCEL, DISCREPANCY, KEEP, cancellation_decision


def test_la_cancela_la_fuente_de_mayor_prioridad():
    assert cancellation_decision({"bp": "cancelled", "wiki": "scheduled"}) == CANCEL


def test_solo_la_publica_una_fuente_secundaria():
    assert cancellation_decision({"bp": "scheduled", "wiki": "cancelled"}) == DISCREPANCY
    assert cancellation_decision({"bp": "live", "cdl": "cancelled"}) == DISCREPANCY


def test_si_la_principal_no_publica_el_partido_manda_la_siguiente():
    # Entre las que publican el partido, la de mayor prioridad es la Wiki.
    assert cancellation_decision({"wiki": "cancelled", "cdl": "scheduled"}) == CANCEL
    assert cancellation_decision({"wiki": "scheduled", "cdl": "cancelled"}) == DISCREPANCY


def test_sin_cancelaciones_no_pasa_nada():
    assert cancellation_decision({"bp": "finished", "wiki": "finished"}) == KEEP
    assert cancellation_decision({}) == KEEP


def test_todas_las_combinaciones_de_las_tres_fuentes():
    # Se cancela si y solo si la de mayor prioridad que publica el partido dice "cancelled".
    import itertools
    states = ("absent", "scheduled", "cancelled")
    for bp, wiki, cdl in itertools.product(states, repeat=3):
        published = {src: st for src, st in (("bp", bp), ("wiki", wiki), ("cdl", cdl)) if st != "absent"}
        top = next((published[src] for src in ("bp", "wiki", "cdl") if src in published), None)
        anyone = "cancelled" in published.values()
        expected = CANCEL if top == "cancelled" else DISCREPANCY if anyone else KEEP
        assert cancellation_decision(published) == expected, published

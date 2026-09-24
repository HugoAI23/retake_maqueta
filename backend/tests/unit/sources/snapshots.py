"""Lectura de las muestras recortadas de la fase F0 (`tests/snapshots/`)."""

import json
from pathlib import Path

SNAPSHOTS = Path(__file__).resolve().parents[2] / "snapshots"


def load(path: str) -> dict:
    """Contenido de una muestra (sin la cabecera de fuente, dirección y fecha)."""
    return json.loads((SNAPSHOTS / path).read_text(encoding="utf-8"))["content"]


def next_data_html(page_props: dict) -> str:
    """Página mínima con el JSON incrustado de Next.js, como las de BreakingPoint."""
    payload = json.dumps({"props": {"pageProps": page_props}})
    return f'<html><body><script id="__NEXT_DATA__" type="application/json">{payload}</script></body></html>'

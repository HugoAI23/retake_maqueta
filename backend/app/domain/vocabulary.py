"""Listas cerradas de la spec 002, compartidas por el dominio y los modelos.

Viven en el dominio para que las reglas no dependan de la base de datos (plan D-5);
los modelos (app.db.models.types) las importan desde aquí.
"""

# Fuentes de datos (RF-66): BreakingPoint.gg, Call of Duty Esports Wiki y web oficial de la CDL.
SOURCES = ("bp", "wiki", "cdl")

# Estados de un partido en Retake (RF-35).
MATCH_STATUSES = ("scheduled", "live", "finished")

# Fases cerradas (RF-31). Un partido con otra fase se guarda sin fase (RF-134).
PHASES = ("week", "group", "winners_bracket", "losers_bracket", "grand_final")

# Roles de jugador (RF-26). Sin rol = nulo (RF-27).
ROLES = ("SMG", "AR")

# Origen de un equipo aún por decidir (RF-84).
ORIGIN_OUTCOMES = ("winner", "loser")

# Tipos de enlace entre referencias externas declarados por una fuente (RF-114, RF-131).
LINK_TYPES = ("same_as", "predecessor")

# --- Spec 003 (obtención y actualización de los datos) ---------------------------------------
# Las necesitan las restricciones de la migración de la fase F1; T-016 añadirá los umbrales.

# Por qué una observación no es válida (plan D-8): un valor imposible pasa a ausente
# (RF-100 de la 002); uno ilegible cede el turno a otra fuente o conserva el valor (RF-48, RF-49).
INVALID_REASONS = ("impossible", "unreadable")

# Conjuntos de datos que avisan de sus cambios y de su frescura (plan §2.5, RF-89, RF-158).
DATASETS = ("live", "matches", "standings", "franchises", "players", "events", "championships", "season")

# Tipos de consulta del planificador (plan §5).
SYNC_JOBS = (
    "initial_load", "live", "pre_match", "regular", "finished_matches", "history", "daily_summary", "cleanup",
)

# Resultado de una consulta a una fuente (plan §3.1).
RUN_OUTCOMES = ("success", "partial", "failure", "forbidden")

# Peticiones del administrador (plan §3.4): tipo, estado y resultado (RF-100 a RF-111).
REQUEST_KINDS = ("source_refresh", "history_reread")
REQUEST_STATUSES = ("pending", "running", "done")
REQUEST_RESULTS = ("success", "partial", "failure", "forbidden")

# Tipos de incidencia (glosario de la spec 003).
INCIDENT_KINDS = (
    "query_failed",        # consulta fallida (RF-141)
    "data_rejected",       # dato rechazado (RF-142)
    "query_forbidden",     # consulta prohibida por las normas de la fuente (RF-143)
    "match_disappeared",   # partido desaparecido (RF-144)
    "record_retained",     # registro retenido sin enlazar (RF-145)
    "cancel_discrepancy",  # cancelación publicada solo por una fuente secundaria (RF-146)
    "origin_blocked",      # origen bloqueado tras 5 intentos fallidos (RF-133)
)

# Formatos de logo admitidos, sin código ejecutable (RF-68), y tamaño máximo (RF-69).
LOGO_MEDIA_TYPES = ("image/png", "image/jpeg", "image/webp")
LOGO_MAX_BYTES = 1_048_576

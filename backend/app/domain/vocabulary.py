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

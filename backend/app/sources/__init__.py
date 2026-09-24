"""Conectores de las fuentes de datos (plan de la spec 003, §2.2).

Cada conector traduce lo que publica una fuente a registros de fuente (`SourceRecord`, el
contrato de la 002) y nunca escribe en la base de datos: eso lo hace la ingesta (plan D-1).
"""

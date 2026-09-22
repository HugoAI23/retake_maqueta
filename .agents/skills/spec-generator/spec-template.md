# Spec: [Nombre de la Funcionalidad]

- **ID**: `[NNN-nombre-funcionalidad]`
- **Fecha**: `[YYYY-MM-DD]`
- **Estado**: `[Borrador | En Revisión | Aprobado]`

---

## 1. Contexto y Propósito (Por Qué)

Describe el problema que resuelve esta funcionalidad y el valor que aporta al usuario dentro de la plataforma Retake. No incluyas detalles técnicos, arquitecturas ni nombres de archivos aquí.

---

## 2. Requisitos Funcionales (Notación EARS)

Cada criterio de aceptación debe usar exclusivamente uno de los 5 patrones EARS y ser verificable de forma unívoca:

* **RF-1 (Ubicuo)**: EL SISTEMA [acción continua o propiedad que siempre se cumple].
* **RF-2 (Dirigido por evento)**: CUANDO [el usuario hace clic / ocurre disparador], EL SISTEMA [respuesta inmediata].
* **RF-3 (Estado)**: MIENTRAS [se encuentre en estado X / cargando / sin conexión], EL SISTEMA [comportamiento específico].
* **RF-4 (Opcional)**: DONDE [el usuario seleccione filtrar por rol SMG / active modo X], EL SISTEMA [comportamiento condicional].
* **RF-5 (No deseado / Casos Límite)**: SI [la predicción falla / no hay datos disponibles / entrada inválida], ENTONCES EL SISTEMA [gestión del error y feedback visual].

---

## 3. Casos Límite y Manejo de Errores

Detalle de escenarios inusuales y cómo debe reaccionar el sistema:
1. **Datos vacíos o no disponibles**: Qué ve el usuario cuando aún no hay estadísticas registradas para esa jornada o jugador.
2. **Entradas no válidas**: Restricciones de formato o rango y feedback inmediato.
3. **Peticiones lentas o interrumpidas**: Comportamiento ante pérdida de conexión o latencia.

---

## 4. Fuera de Alcance

Lista explícita de lo que **NO** se implementará en esta funcionalidad para prevenir *scope creep*:
* [Elemento 1 que no se incluye en esta fase]
* [Elemento 2 que queda para versiones posteriores]

---

## 5. Dudas y Aclaraciones Pendientes

Elementos que requieren confirmación de Hugo antes de cerrar la spec:
* `[NECESITA ACLARACIÓN: ...]`

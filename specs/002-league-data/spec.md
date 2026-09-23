# Spec: Datos de la Liga

- **ID**: `002-league-data`
- **Fecha**: `2026-09-21`
- **Estado**: `En Revisión`

---

## 1. Contexto y Propósito (Por Qué)

Retake es un centro de estadísticas y predicciones de la Call of Duty League. Todas sus secciones (cinta de marcadores, spotlight, cuadrícula de partidos, páginas de equipos, jugadores y torneos, y más adelante los modelos de Machine Learning) consumen la misma información de la liga.

Esta spec define **qué información de la liga existe en Retake, con qué nivel de detalle y cómo se comporta cuando falta o cambia**, para que todas las secciones hablen del mismo equipo, el mismo jugador y el mismo partido. No define cómo se obtiene ni cómo se actualiza esa información (spec 003), ni cómo se presenta en pantalla (specs 004 en adelante).

Alcance temporal: detalle completo de la **temporada actual** y, de temporadas anteriores, únicamente el **historial de campeonatos**.

---

## 2. Requisitos Funcionales (Notación EARS)

### 2.1 Temporada actual

* **RF-1 (Ubicuo)**: EL SISTEMA mantendrá equipos, jugadores, eventos, partidos, estadísticas y posiciones únicamente de la temporada actual.
* **RF-2 (Estado)**: MIENTRAS ningún partido de una nueva temporada haya comenzado, EL SISTEMA considerará como temporada actual la temporada anterior.
* **RF-3 (Dirigido por evento)**: CUANDO comience el primer partido de una nueva temporada, EL SISTEMA pasará a considerarla la temporada actual.

### 2.2 Historial de campeonatos

* **RF-4 (Ubicuo)**: EL SISTEMA mantendrá, para cada temporada desde 2013 hasta la actual, la clasificación final del campeonato de la liga.
* **RF-5 (Ubicuo)**: EL SISTEMA registrará para cada equipo de la clasificación final su lugar, el premio obtenido, el porcentaje de la bolsa que representa, el título del juego y la fecha de la final.
* **RF-6 (Ubicuo)**: EL SISTEMA asociará a cada equipo de la clasificación final la lista de jugadores de su roster en ese campeonato.
* **RF-7 (Ubicuo)**: EL SISTEMA registrará el premio de un campeonato una sola vez por equipo, sin repetirlo ni multiplicarlo por el número de jugadores del roster.
* **RF-8 (Opcional)**: DONDE el lugar de un equipo sea un rango compartido (ej. `9-12`), EL SISTEMA mostrará el rango tal como fue publicado.
* **RF-9 (Opcional)**: DONDE un equipo haya sido descalificado, EL SISTEMA mostrará `DQ` en lugar de un lugar numérico.

### 2.3 Franquicias e identidad visual

* **RF-10 (Ubicuo)**: EL SISTEMA reconocerá como una misma franquicia a un equipo que haya cambiado de nombre.
* **RF-11 (Ubicuo)**: EL SISTEMA mantendrá para cada identidad de una franquicia un nombre corto (ej. `FaZe VGS`), una abreviatura (ej. `VGS`), un logo, un color primario y un color secundario.
* **RF-12 (Ubicuo)**: EL SISTEMA mostrará en cada partido la identidad que la franquicia tenía en la fecha en que se jugó.
* **RF-13 (Ubicuo)**: EL SISTEMA mostrará en cada registro del historial de campeonatos la identidad que la franquicia tenía en la fecha de esa final.
* **RF-14 (No deseado)**: SI una identidad de una franquicia no tiene logo registrado, ENTONCES EL SISTEMA mostrará el logo de la identidad más reciente de esa franquicia.
* **RF-15 (No deseado)**: SI ninguna identidad de la franquicia tiene logo registrado, ENTONCES EL SISTEMA mostrará la abreviatura de la identidad sobre su color primario.

### 2.4 Jugadores

* **RF-16 (Ubicuo)**: EL SISTEMA mostrará a cada jugador con su gamertag actual.
* **RF-17 (Ubicuo)**: EL SISTEMA registrará los gamertags anteriores de cada jugador.
* **RF-18 (Ubicuo)**: EL SISTEMA reconocerá como la misma persona a un jugador de la temporada actual y a un jugador del historial de campeonatos que usó cualquiera de sus gamertags.
* **RF-19 (Ubicuo)**: EL SISTEMA distinguirá como personas diferentes a dos jugadores que hayan usado el mismo gamertag.
* **RF-20 (Ubicuo)**: EL SISTEMA asociará a cada jugador de la temporada actual los campeonatos del historial en los que formó parte de un roster.
* **RF-21 (Ubicuo)**: EL SISTEMA mostrará de cada jugador su nombre real.
* **RF-22 (Ubicuo)**: EL SISTEMA mostrará de cada jugador su país.
* **RF-23 (Ubicuo)**: EL SISTEMA mostrará de cada jugador su edad en años cumplidos a la fecha de consulta.
* **RF-24 (Ubicuo)**: EL SISTEMA no mostrará la fecha de nacimiento exacta de ningún jugador.
* **RF-25 (No deseado)**: SI un dato personal de un jugador (nombre real, país o edad) no está registrado, ENTONCES EL SISTEMA indicará que el dato no está disponible en lugar de dejar el espacio en blanco.
* **RF-26 (Ubicuo)**: EL SISTEMA asignará a cada jugador un único rol, `SMG` o `AR`, durante toda la temporada actual.
* **RF-27 (No deseado)**: SI no se conoce el rol de un jugador, ENTONCES EL SISTEMA lo mostrará como `Sin rol`.
* **RF-28 (Estado)**: MIENTRAS un jugador esté como `Sin rol`, EL SISTEMA lo excluirá de cualquier clasificación o ranking por rol.
* **RF-29 (Ubicuo)**: EL SISTEMA atribuirá las estadísticas de un jugador en un partido al equipo en el que jugaba en la fecha de ese partido.

### 2.5 Eventos y partidos

* **RF-30 (Ubicuo)**: EL SISTEMA asignará cada partido de la temporada actual a un evento (ej. Major 2 Qualifiers, Major 2, Champs).
* **RF-31 (Ubicuo)**: EL SISTEMA asignará cada partido a una fase dentro de su evento (ej. semana, grupo, winners bracket, losers bracket, final).
* **RF-32 (Ubicuo)**: EL SISTEMA registrará para cada partido los dos equipos que lo disputan.
* **RF-33 (Ubicuo)**: EL SISTEMA registrará para cada partido su fecha y hora programadas.
* **RF-34 (Ubicuo)**: EL SISTEMA registrará para cada partido su formato expresado como "al mejor de N mapas".
* **RF-35 (Ubicuo)**: EL SISTEMA asignará a cada partido exactamente uno de estos estados: `programado`, `en vivo` o `finalizado`.
* **RF-36 (Estado)**: MIENTRAS un partido esté `en vivo`, EL SISTEMA mantendrá el número de mapas ganados por cada equipo.
* **RF-37 (Estado)**: MIENTRAS un partido esté `en vivo`, EL SISTEMA mantendrá el marcador del mapa en curso en la unidad propia de su modo (ej. puntos en Hardpoint, rondas en Search & Destroy).
* **RF-38 (Dirigido por evento)**: CUANDO un partido pase a `finalizado`, EL SISTEMA registrará el marcador final de la serie.
* **RF-39 (Dirigido por evento)**: CUANDO un partido pase a `finalizado`, EL SISTEMA registrará el equipo ganador.
* **RF-40 (Ubicuo)**: EL SISTEMA registrará para cada mapa jugado su posición en la serie, su modo, el nombre del mapa, el marcador final y el equipo ganador.

### 2.6 Estadísticas de jugadores por mapa

* **RF-41 (Ubicuo)**: EL SISTEMA registrará para cada jugador en cada mapa jugado: kills, deaths, K/D, daño y asistencias.
* **RF-42 (Opcional)**: DONDE el modo del mapa sea Hardpoint, EL SISTEMA registrará además el hill time y el contested hill time de cada jugador.
* **RF-43 (Opcional)**: DONDE el modo del mapa sea Search & Destroy, EL SISTEMA registrará además los first bloods, first deaths, plants y defuses de cada jugador.
* **RF-44 (Opcional)**: DONDE el modo del mapa sea Overload, EL SISTEMA registrará además las zone captures y los overloads de cada jugador.
* **RF-45 (Ubicuo)**: EL SISTEMA presentará únicamente las estadísticas que publica la fuente, sin métricas derivadas.
* **RF-46 (No deseado)**: SI una estadística concreta de un jugador no viene en la fuente, ENTONCES EL SISTEMA la mostrará como `No disponible` en lugar de 0.
* **RF-47 (No deseado)**: SI un partido está `finalizado` y no tiene estadísticas por mapa, ENTONCES EL SISTEMA mostrará su marcador final acompañado del aviso "Estadísticas pendientes".
* **RF-48 (Dirigido por evento)**: CUANDO se registren las estadísticas por mapa de un partido que mostraba "Estadísticas pendientes", EL SISTEMA retirará el aviso.

### 2.7 Tabla de posiciones

* **RF-49 (Ubicuo)**: EL SISTEMA mantendrá la tabla de posiciones oficial de la temporada actual con la posición y los puntos CDL de cada equipo.
* **RF-50 (Ubicuo)**: EL SISTEMA mostrará los puntos CDL exactamente como los publica la liga, sin recalcularlos a partir de resultados.
* **RF-51 (No deseado)**: SI la liga aún no ha publicado posiciones para la temporada actual, ENTONCES EL SISTEMA indicará que la tabla de posiciones todavía no está disponible.

---

## 3. Casos Límite y Manejo de Errores

1. **Datos vacíos o no disponibles**:
   - Partido finalizado sin estadísticas por mapa → marcador final con aviso "Estadísticas pendientes" (RF-47, RF-48).
   - Estadística concreta ausente en la fuente → `No disponible`, nunca 0; un 0 significa "no lo hizo", un vacío significa "no se sabe" (RF-46).
   - Dato personal de un jugador sin registrar → "no disponible" (RF-25).
   - Rol desconocido → `Sin rol` y exclusión de rankings por rol (RF-27, RF-28).
   - Tabla de posiciones aún no publicada → aviso explícito (RF-51).
2. **Cambio de temporada**:
   - Entre temporadas se sigue mostrando la anterior hasta que comience el primer partido de la nueva (RF-2, RF-3).
   - Al cambiar, el detalle de la temporada que termina deja de mantenerse y solo permanece su clasificación final en el historial de campeonatos (RF-1, RF-4).
3. **Cambios de identidad**:
   - Una franquicia que cambia de nombre sigue siendo la misma (RF-10), pero cada partido y cada final conservan el nombre, logo y colores de su fecha (RF-12, RF-13).
   - Si a una identidad le falta el logo se usa el más reciente de la franquicia, y si no existe ninguno, la abreviatura sobre su color primario (RF-14, RF-15).
   - Un jugador que cambia de gamertag sigue siendo la misma persona (RF-17, RF-18); dos personas con el mismo gamertag se mantienen separadas (RF-19).
   - Un jugador traspasado a mitad de temporada conserva sus estadísticas en el equipo con el que las hizo (RF-29).
4. **Datos del historial con formato especial**:
   - Lugares compartidos (`9-12`) y descalificaciones (`DQ`) se muestran tal como fueron publicados (RF-8, RF-9).
   - El premio es del equipo, no de cada jugador; nunca se suma por jugador (RF-7). Detectado en el spike: sumar por jugador daba $3,200,000 a FaZe VGS 2026 en vez de $800,000.
5. **Peticiones lentas o interrumpidas**: fuera del alcance de esta spec; los estados de carga pertenecen a la spec 001 y a cada sección visual.

---

## 4. Fuera de Alcance

* Estadísticas, rosters, partidos y posiciones detalladas de temporadas anteriores (solo se conserva el historial de campeonatos).
* Métricas derivadas o calculadas (KD ajustado, +/- acumulado, daño por minuto, etc.); se definirán en specs posteriores.
* Estados de partido `pospuesto`, `cancelado` y `forfeit`.
* Estadísticas de jugadores actualizadas en vivo durante un mapa.
* Rol `Flex` y roles de jugador por mapa o por evento.
* Cambio manual de la temporada actual.
* Cálculo propio de la tabla de posiciones.
* Fecha de nacimiento exacta y redes sociales (Twitch, Twitter) de los jugadores.
* Fotografías de jugadores.
* Nombre completo de las franquicias (ej. "FaZe Vegas"); se usa el nombre corto y la abreviatura.
* Dónde se usa el nombre corto y dónde la abreviatura; lo decide cada spec visual (004 en adelante).
* Cómo se obtienen, cargan y actualizan los datos (spec 003).
* Cómo se presentan los datos en pantalla (specs 004 en adelante).
* Predicciones y modelos de Machine Learning (specs 013–015).

---

## 5. Dudas y Aclaraciones Pendientes

Todas las dudas se resolvieron con Hugo el 2026-09-21:

| # | Duda | Decisión | Requisitos |
|---|---|---|---|
| 1 | Temporada actual entre temporadas | La anterior, hasta que comience el primer partido de la nueva | RF-2, RF-3 |
| 2 | Roles posibles y rol desconocido | Solo `SMG` y `AR`; si no se conoce, `Sin rol` y fuera de rankings por rol | RF-26 a RF-28 |
| 3 | Identidad sin logo | Logo de la identidad más reciente; si no hay, abreviatura sobre color primario | RF-14, RF-15 |
| 4 | Estadística vacía en la fuente | `No disponible`, nunca 0 | RF-46 |
| 5 | Campeón histórico que sigue activo | Es el mismo jugador; se registran sus gamertags anteriores | RF-17 a RF-20 |
| 6 | Nombre visible del equipo | Nombre corto (`FaZe VGS`) y abreviatura (`VGS`) | RF-11 |

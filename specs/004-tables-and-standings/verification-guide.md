# Guía de verificación manual — Spec 004

Guía paso a paso para que Hugo compruebe cada requisito de la spec 004 (constitución §5, tarea T-032). Cada fila dice **dónde** mirar, **qué** hacer y **qué** resultado esperar. Lo que se ve a simple vista (animaciones, colores, burbuja) se mira en el **navegador**; el resto tiene además su prueba automática.

Abreviaturas de las órdenes, desde la raíz del repositorio:

- **pt** = `uv run --directory backend pytest` (añade la ruta del archivo y `-v`).
- **vt** = `npx vitest run` (añade la ruta del archivo).
- **pw** = `npx playwright test` (añade la ruta del archivo; `-g "texto"` elige una prueba).

## Preparación

1. Todas las pruebas en verde antes de empezar:
   ```bash
   uv run --directory backend pytest
   ```
   ```bash
   npm test
   ```
   ```bash
   npx playwright test
   ```
2. **Datos reales** (base `retake`, solo se lee; el `retake sync` puede seguir en marcha), dos terminales:
   ```bash
   uv run --directory backend uvicorn app.main:app --port 8000
   ```
   ```bash
   npm run dev
   ```
   Abrir `http://localhost:5173/standings`.
3. **Datos de prueba** (base `retake_guia`, preparada como en la guía de la 002): en la app, arranques `retake-api-guia` y `retake-dev-guia` de `.claude/launch.json`, o en dos terminales:
   ```bash
   export DATABASE_URL="$(grep '^DATABASE_URL=' backend/.env | cut -d= -f2- | sed 's#/retake$#/retake_guia#')" SOURCE_MODE=fixtures
   ```
   ```bash
   uv run --directory backend uvicorn app.main:app --port 8002
   ```
   ```bash
   RETAKE_API_TARGET=http://localhost:8002 npx vite --port 5174
   ```
   Abrir `http://localhost:5174/standings`.
4. **VoiceOver** (para las filas del lector): Cmd+F5. **Reducir movimiento**: Ajustes del Sistema → Accesibilidad → Pantalla → Reducir movimiento.

## Guía por fases

| Fase | Qué comprobar |
|---|---|
| F0 | vt `src/config/designTokens.test.js src/i18n/dictionaries src/blocks/blocks.test.jsx`: colores con su contraste, textos en los dos idiomas y esqueleto de tabla. |
| F1 | `http://localhost:8002/api/standings` (`retake_guia`): Equipo A `series 3–0, maps 8–0`, Equipo B `0–3, 0–8`, FaZe VGS `1–0, 5–2`, OpTic TEX `0–1, 2–5`, el resto `0–0`. `http://localhost:8000/api/standings` (reales): la fila 10 es «Boston Breach». |
| F2 | vt `src/tables`: orden, formato, orden conservado, tabla, nombre recortado y celda de equipo. |
| F3 | vt `src/tables/useTableMotion.test.jsx src/motion`: entrada, contadores, resaltado, recolocación y reducir movimiento. |
| F4 | `/standings` con datos reales y con `retake_guia` (filas de §2.7). |
| F5 | pw `e2e/standings.spec.js` (anchos, teclado, Atrás/Adelante, burbuja, reducir movimiento, zoom, idiomas y axe), checklist de seguridad y esta guía completa. |

---

## 2.1 Tablas de datos

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-1 | Navegador | Abrir `/standings`. | Fila de cabecera con Pos., Equipo, Puntos, Series, Mapas y ±Mapas. |
| RF-2 | Navegador | Entrar desde el menú. | Filas por posición, de la 1 a la última. |
| RF-3 | Navegador | Pulsar «Puntos» tres veces. | ▼ (de mejor a peor), ▲ (de peor a mejor) y vuelta al orden por posición, sin flecha. |
| RF-4 | Navegador | Con Puntos ▲, pulsar «Series». | Series empieza en ▼ (de mejor a peor). |
| RF-5 | Prueba | vt `src/tables/useTableMotion.test.jsx -t "no se repite"` · vt `src/pages/StandingsPage.states.test.jsx -t "se actualiza en silencio"` | Con datos nuevos, el orden elegido no cambia. |
| RF-6 | Navegador + VoiceOver | Ordenar por Puntos y llevar el foco a la cabecera. | Flecha ▼ junto a «Puntos»; VoiceOver lee «Puntos, ordenada de mejor a peor». |
| RF-7 | Prueba | vt `src/tables/sortRows.test.js -t empates` | Filas con el mismo valor conservan el orden por defecto. |
| RF-7a | Navegador | Pulsar «Equipo». | Orden alfabético sin distinguir mayúsculas ni acentos, y «Team 2» antes que «Team 10» (vt `src/tables/sortRows.test.js -t text`). |
| RF-8 | Navegador | Pulsar «Series» (datos reales). | Riyadh Falcons (27–22, 55 %) antes que Toronto KOI (26–25, 51 %), aunque Toronto tiene más puntos. |
| RF-9 | Navegador (`retake_guia`) | Pulsar «Series» y luego otra vez. | En los dos sentidos, los equipos con `0–0` van detrás. |
| RF-10 | Navegador | Ordenar por Mapas; cambiar a EN y estrechar la ventana por debajo de 1024 px. | Sigue ordenada por Mapas (Maps). |
| RF-11 | Navegador | Ordenar por Series, ir a Partidos y volver con Atrás; luego Adelante y Atrás. | Vuelve ordenada por Series. |
| RF-11a | Navegador | Ordenar, recargar la página; ordenar, ir a Partidos y volver por el menú. | En los dos casos, orden por posición. |
| RF-12 | Navegador | Ventana a 320 px. | La tabla se desliza dentro de su caja; la página no se desplaza en horizontal (pw `-g "a 320 px"`). |
| RF-13 | Navegador | A 320 px, deslizar la tabla a la izquierda. | Pos. y Equipo se quedan fijas; entran Mapas y ±Mapas. |

## 2.2 Equipos y jugadores en las tablas

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| §2.2 | Navegador | Mirar la columna Equipo. | Cada equipo con su logo; uno sin logo (p. ej. «Cloud9 NY» en `retake_guia`) lleva la abreviatura o el nombre sobre su color. |
| RF-14 | Navegador | Ventana de 1024 px o más. | Insignia y nombre corto («OpTic Texas»). |
| RF-15 | Navegador | Ventana de 1023 px o menos. | Insignia y abreviatura («TX»). |
| RF-16 | VoiceOver | A menos de 1024 px, recorrer la columna Equipo. | Lee el nombre corto («OpTic Texas»), no «TX». |
| RF-17 | Navegador | Ventana justo por encima de 1024 px (o datos con un nombre largo). | Si un nombre se corta con «…», pasar el puntero lo muestra entero en una burbuja (pw `-g "nombre recortado"`). |
| RF-17a | Navegador | Recorrer la tabla con Tab. | El nombre recortado recibe el foco y abre la burbuja; los que caben, no. |
| RF-17b | Navegador | Con la burbuja abierta: pasar el puntero a la burbuja; pulsar Escape. | Sigue abierta con el puntero encima; Escape la cierra sin mover el foco. |
| RF-18 | Navegador | Pulsar el nombre de un equipo. | No navega: es texto, sin enlace. |

## 2.3 Balances y diferencias

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-20 | Navegador | Columnas Series y Mapas. | «43–14», con una raya entre las cifras. |
| RF-21 | Navegador | Columna ±Mapas en ES y en EN. | «+72», «−9» (signo menos, no guion) y «0» sin signo, en los dos idiomas (vt `src/tables/tableFormat.test.js`). |
| RF-22 | Navegador | Columna ±Mapas. | Positivas en verde, negativas en rojo y 0 en el color del texto; contraste comprobado en vt `src/config/designTokens.test.js`. |
| RF-23 | Prueba | vt `src/tables/tableFormat.test.js -t "dígitos"` | 12.345 en español y 12,345 en inglés. |

## 2.4 Carga, error y vacío de las tablas

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-24 | Navegador | Recargar `/standings` con la red lenta (DevTools → Network → Slow 3G). | Mientras carga, un esqueleto con forma de tabla. |
| RF-25 | Navegador | Parar el backend y recargar; arrancarlo y pulsar «Reintentar». | Aviso de error con «Reintentar»; al pulsarlo, la tabla. Sin red: aviso «Sin conexión» y la tabla sigue (vt `src/pages/StandingsPage.states.test.jsx`). |
| RF-26 | Prueba | vt `src/pages/StandingsPage.states.test.jsx -t "RF-51"` | Sin tabla, el mensaje de vacío de Posiciones en su lugar. |
| RF-27 | Prueba | vt `src/pages/StandingsPage.states.test.jsx -t "silencio"` | Con un cambio de la tabla o de los partidos, se actualiza sin esqueleto ni avisos; si falla, conserva los datos. |

## 2.5 Animaciones de las tablas

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-28 | Navegador | Entrar en Posiciones desde el menú. | Las filas aparecen escalonadas y Puntos, Series, Mapas y ±Mapas cuentan desde 0. |
| RF-28a | Navegador | La misma entrada, mirando con atención. | Primero el fundido de la página; después, la entrada de la tabla. |
| RF-28b | Prueba | vt `src/tables/useTableMotion.test.jsx -t "no se repite"` | Al actualizarse, no se repite la entrada. |
| RF-28c | Prueba | vt `src/tables/useTableMotion.test.jsx -t "valor nuevo"` | Con datos a mitad de la entrada, las cifras terminan en el valor nuevo. |
| RF-28d | Navegador | Ventana baja (unos 500 px) y entrar en Posiciones; bajar enseguida. | Las filas de abajo ya están con su valor, sin animar. |
| RF-29 | Prueba | pw `e2e/standings.spec.js -g "menos de 800 ms"` | La entrada acaba en ≤ 800 ms (con la transición, menos de 1,4 s). |
| RF-30 | Prueba | vt `src/tables/useTableMotion.test.jsx -t "resalta"` | La celda que cambia se resalta y el fondo se desvanece. *Con datos reales, se ve cuando la tabla cambia durante la temporada.* |
| RF-31 | Navegador | Pulsar «Series» y luego «Pos.». | Las filas se deslizan a su sitio nuevo, sin saltar la vista. |
| RF-31a | Prueba | vt `src/tables/useTableMotion.test.jsx -t "foco"` | La fila con el foco lo conserva al recolocarse, sin mover la vista. |
| RF-32 | Prueba | vt `src/tables/useTableMotion.test.jsx -t "300 ms"` | Resaltado y recolocación en ≤ 300 ms. |
| RF-33 | Navegador | Activar reducir movimiento y entrar en Posiciones; ordenar. | Ninguna animación: la tabla aparece directamente y las filas cambian de sitio al instante. |
| RF-34 | VoiceOver | Entrar en Posiciones y leer enseguida una cifra. | Lee el valor final (no «0»); se puede ordenar durante la entrada. |

## 2.6 Accesibilidad e idioma de las tablas

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-35 | Prueba | pw `e2e/standings.spec.js -g "axe"` | Sin incumplimientos AA en es y en, a 320 y 1440 px, ordenada y con la burbuja abierta. |
| RF-36 | VoiceOver | Con VO+flechas, moverse por las celdas. | Cada cifra se lee con su columna y su equipo (p. ej. «Puntos, OpTic Texas, 575»). |
| RF-36a | VoiceOver | Moverse por una columna de cifras. | Cada fila se identifica por el equipo. |
| RF-37 | Navegador | Solo con Tab, Intro y Espacio: ordenar por Puntos. | Mismo ciclo que con el ratón (pw `-g "teclado"`). |
| RF-38 | Navegador | Pasar el puntero, tabular y mantener pulsada una cabecera. | Fondo en hover, contorno de foco amarillo y estado pulsado. |
| RF-39 | Navegador | Zoom al 200 % (Cmd +) con la ventana a 1280 px. | Todo visible y usable; se puede ordenar (pw `-g "200 %"`). |
| RF-40 | Navegador | Cambiar a EN. | «Standings», «2026 Season», cabeceras en inglés y avisos en inglés. |

## 2.7 Sección Posiciones

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-41 | Navegador (reales) | Abrir `/standings`. | Los 12 equipos de la tabla de 2026, sin invitados (ni OMiT ni ROC Esports). |
| RF-41a | Navegador (reales) | Fila 10. | «Boston Breach» (BOS) con su logo, no «M80 Boston» (identidad posterior al último partido). |
| RF-41b | Prueba | pt `backend/tests/integration/api/test_004_standings.py -k identidad_vigente` | Una franquicia sin partidos en la temporada lleva su identidad vigente. |
| RF-41c | Prueba | vt `src/pages/StandingsPage.table.test.jsx -t "publicada"` | Una franquicia que no está en la tabla publicada no sale. |
| RF-42 | Navegador | Cabecera. | «Posiciones» y debajo «Temporada 2026», el mismo año que el pie. |
| RF-42a | Prueba | vt `src/pages/StandingsPage.header.test.jsx -t "sin temporada"` | Sin temporada actual: solo el título y el texto de RF-51. |
| RF-42b | Navegador | Pestaña del navegador en ES y EN. | «Posiciones · Retake» / «Standings · Retake». |
| RF-43 | Navegador | Cabeceras. | Pos., Equipo, Puntos, Series, Mapas y ±Mapas, en ese orden. |
| RF-44 | Navegador (reales) | Primeras filas. | OpTic Texas 1.º con 575; LA Thieves 2.º con 515, como en `/api/standings`. |
| RF-44a | Prueba | vt `src/pages/StandingsPage.table.test.jsx -t "No disponible"` | Sin posición o sin puntos: «No disponible» en la celda. |
| RF-45 | Navegador (reales) | Series y Mapas de OpTic Texas. | 43–14 y 152–80. |
| RF-45a | Prueba | vt `src/pages/StandingsPage.table.test.jsx -t "No disponible"` · pt `backend/tests/integration/api/test_004_standings.py -k no_esta_disponible` | Sin balance: «No disponible» en Series, Mapas y ±Mapas, y detrás al ordenar. |
| RF-46 | Navegador (reales) | ±Mapas de OpTic Texas. | +72 (152 − 80). |
| RF-47 | Navegador (`retake_guia`) | Últimas filas, a ≥ 1024 y a < 1024 px. | Los dos equipos de la 13, en orden alfabético del texto que se ve (FXA antes que FXB). |
| RF-48 | Navegador + VoiceOver (`retake_guia`) | Las dos filas de la 13. | Las dos muestran «13»; VoiceOver lee «13.º, compartido» (en inglés, «13, tied»). |
| RF-49 | Navegador | Pulsar cada cabecera una vez. | Pos. de menor a mayor; Equipo alfabético; Puntos y ±Mapas de mayor a menor; Series y Mapas por % de victorias. |
| RF-50 | Navegador | A 320 px, deslizar la tabla. | Pos. y Equipo fijas. |
| RF-50a | Navegador | Entrar desde el menú. | Cuentan Puntos, las dos cifras de Series y de Mapas, y ±Mapas con su signo; la posición no. |
| RF-50b | VoiceOver | Moverse por la fila. | La cabecera de cada fila es el equipo. |
| RF-51 | Prueba | vt `src/pages/StandingsPage.states.test.jsx -t "RF-51"` | Sin tabla, o sin puntos para ningún equipo: «La tabla de posiciones todavía no está disponible». *En diciembre, al empezar 2027, se verá con datos reales.* |
| RF-51a | Prueba | vt `src/pages/StandingsPage.season.test.jsx` | Al cambiar la temporada con la página abierta: año nuevo, orden por defecto y entrada, o texto de RF-51; sin anuncios. *Con datos reales, en diciembre (T-089 de la 003).* |
| RF-52 | Navegador | Menú → Posiciones. | Ya no dice «Próximamente»; las demás secciones sí. |
| RF-53 | VoiceOver | Con la tabla abierta, esperar un cambio (o pw/vt `-t "silencio"`). | Ningún anuncio de los cambios de la tabla. |
| RF-53a | Prueba | vt `src/pages/StandingsPage.states.test.jsx -t "silencio"` | Se actualiza con los cambios de `standings` y de `matches`. |
| RF-53b | Navegador (reales) | Dejar la página abierta. | Recoge los cambios en ≤ 5 min (ciclo del resto de datos) o al avisar el canal. |
| RF-53c | Prueba | vt `src/pages/StandingsPage.header.test.jsx -t "sin actualizar"` | Si cualquiera de los dos conjuntos está sin actualizar: aviso debajo de la última actualización. |
| RF-53d | Navegador | Bajo «Temporada 2026». | «Actualizado: <fecha y hora>». |
| RF-53e | Prueba | vt `src/pages/StandingsPage.header.test.jsx -t "última actualización"` · pt `backend/tests/integration/api/test_004_standings.py -k changed_at` | Última actualización = el cambio más reciente de la tabla o de sus partidos contados; sin tabla, el de los dos conjuntos. *Con datos reales se ve la hora de la consulta horaria de BreakingPoint: problema de la 003 anotado sin corregir.* |

## Cambio C-29 en la spec 002 (RF-136 a RF-139)

| RF | Dónde | Acción | Resultado esperado |
|---|---|---|---|
| RF-136 | Prueba · psql (reales) | pt `backend/tests/unit/domain/test_season_balance.py` · la consulta de abajo | Series con todos los partidos finalizados, también contra invitados: Vancouver Surge 10–27 incluye su 0–3 contra OMiT (CDL Major 3). |
| RF-137 | Navegador (`retake_guia`) | Equipo A. | Mapas 8–0: 3–0, 3–0 y 2–0 (un 3–1 sumaría 3 y 1). |
| RF-138 | Prueba | pt `backend/tests/unit/domain/test_season_balance.py -k sin_marcador` | Con ganador y sin marcador: cuenta la serie, no los mapas. |
| RF-138a | Prueba | pt `backend/tests/unit/domain/test_season_balance.py -k ni_marcador` | Sin ganador ni marcador: no cuenta. |
| RF-139 | Prueba | pt `backend/tests/integration/api/test_004_standings.py -k no_esta_disponible` | Sin partidos de la temporada: `series` y `maps` nulos en todas las filas. |

Consulta de RF-136 con los datos reales (solo lectura):

```bash
psql -h localhost -d retake -c "select (select i.short_name from identity i where i.franchise_id = f.id order by i.valid_from desc limit 1) as invitado, e.name as evento, count(*) as partidos from match m join event e on e.id = m.event_id join match_slot s on s.match_id = m.id join franchise f on f.id = s.franchise_id where f.is_guest and m.status = 'finished' group by 1, 2 order by 2, 1"
```

Muestra los invitados de 2026 y en qué evento jugaron (todos en el «CDL Major 3 Tournament»; no hay ninguno en un Minor).

---

## Checklist de seguridad (constitución §6, plan §9, T-030)

| Punto | Comprobación | Resultado |
|---|---|---|
| Texto de las fuentes solo como texto | `grep -rn "dangerouslySetInnerHTML\|innerHTML" src/tables src/pages/StandingsPage.jsx` · vt `src/pages/StandingsPage.table.test.jsx -t "HTML"` | Ninguno; un nombre con `<img onerror>` se pinta como texto. |
| Logos solo como `<img>` y con dirección propia | `src/tables/TeamCell.jsx`: `<img src={badge.src}>` con `/api/logos/<huella>` de la 003 | Sí. |
| Colores de las fuentes validados | vt `src/pages/StandingsPage.table.test.jsx -t "color primario"` | Un color no válido usa el neutro; nada llega al estilo. |
| Sin SQL concatenado | `app/db/queries.py` y `app/api/views.py`: solo `select()` de SQLAlchemy con parámetros | Sí. |
| `/api/standings` sin parámetros nuevos | `app/api/routes.py` | Sí: solo campos nuevos en la respuesta. |
| Ningún dato personal en la tabla | `StandingOut`: franquicia, identidad, posición, puntos, balance y `changedAt` | Sí. |
| `history.state` | `src/tables/useSortState.js` | Solo la columna, el sentido y la marca de la carga. |

## Comprobación

- **2026-09-26:** Hugo ejecutó las pruebas de cada fase (F0: 301, F1: 32 y la API con `retake_guia` y con los datos reales, F2: 50, F3: 36, F4: 69, F5: 122 de extremo a extremo en `dev` y `prod`), todas en verde, y comprobó en el navegador la sección Posiciones con los datos reales y con `retake_guia`.

## Pendiente que depende del calendario

- RF-51 y RF-51a con datos reales: al empezar la temporada 2027 (diciembre de 2026), junto con T-089 de la 003.
- RF-30 con datos reales: cuando la tabla cambie durante una temporada en marcha.

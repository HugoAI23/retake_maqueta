# Guía de verificación manual — Spec 001

Guía paso a paso para que Hugo compruebe cada requisito en el navegador (constitución §5.1, tarea T-080). Cada fila indica la **vista** que hay que abrir, la **acción** que hay que hacer y el **resultado** esperado.

## Preparación

1. En la raíz del repositorio, instalar las dependencias (solo la primera vez) y arrancar el servidor de desarrollo:
   ```bash
   npm install
   npm run dev
   ```
2. Abrir `http://localhost:5173` en Chrome.
3. Abrir las herramientas de desarrollo (⌥⌘I) y activar la **barra de dispositivos** (⇧⌘M) para cambiar el ancho de la ventana.
4. Para empezar como en una primera visita: en las herramientas de desarrollo, **Application → Local storage → `http://localhost:5173`**, borrar `retake.locale`.
5. Para probar la versión de producción, que es lo que se usa en RF-95:
   ```bash
   npm run build && npm run preview
   ```
   y abrir `http://localhost:4173`.

Pruebas automáticas (deben estar en verde antes de empezar):

```bash
npm test
```

```bash
npm run test:e2e
```

---

## 2.1 Estructura común

| RF | Vista | Acción | Resultado esperado |
|---|---|---|---|
| RF-1 | `/`, `/players`, `/no-existe` | Mirar la página de arriba abajo. | Cinta de marcadores, menú, contenido y pie, en ese orden, en las tres. |
| RF-2 | `/` a 1440 px | Mirar la franja superior. | La cinta ocupa todo el ancho y está justo encima del menú. |
| RF-3 | `/` a 1440 px con poca altura | Hacer scroll hacia abajo. | La cinta y el menú se van con la página; no quedan fijos. |
| RF-4 | Todas las rutas a 320, 1023, 1024 y 1440 px | Intentar desplazarse de lado. | Nunca aparece scroll horizontal. |
| RF-5 | `/` | Poner el sistema operativo en modo claro. | Retake sigue en tema oscuro; no hay opción de tema claro. |

## 2.2 Menú de navegación (1024 px o más)

| RF | Vista | Acción | Resultado esperado |
|---|---|---|---|
| RF-6 | `/` a 1440 px | Leer las entradas. | Inicio, Partidos, Equipos, Jugadores, Torneos, Posiciones, Noticias, Modelos de ML. |
| RF-7 | `/` a 1024 px, en español y en inglés | Mirar la cabecera. | Logo, las ocho entradas y el selector ES/EN en una sola fila, sin cortes. |
| RF-8 | `/` | Comparar las entradas. | Solo Modelos de ML tiene fondo violeta. |
| RF-9 | `/` | Mirar Modelos de ML. | Lleva un icono de nodos conectados junto al nombre. |
| RF-10 | `/` | Mirar Modelos de ML. | Lleva la etiqueta "IA" ("AI" en inglés). |
| RF-11 | Cualquier página | Mirar la izquierda de la cabecera. | Aparece el logo "Retake". |
| RF-12 | `/players` | Pulsar el logo. | Lleva a Inicio. |
| RF-13 | `/` | Todavía no hay archivo de logo, así que se ve el texto "Retake". | El texto enlaza a Inicio. Cuando haya logo, bloquear su petición en Network → *Block request URL* y recargar: vuelve a aparecer el texto. |
| RF-14 | `/` | Pulsar "Equipos". | Lleva a `/teams`. |
| RF-15 | `/teams`, con scroll hacia abajo (ventana baja) | Pulsar "Equipos". | Vuelve al principio de la página en 300 ms como máximo; no se añade ninguna entrada al historial. |

## 2.3 Menú plegado (menos de 1024 px)

| RF | Vista | Acción | Resultado esperado |
|---|---|---|---|
| RF-16 | `/` a 375 px | Mirar la cabecera. | Las entradas no se ven; hay un botón de menú (☰). |
| RF-17 | `/` a 375 px | Mirar la cabecera. | Se ven el logo, "Modelos de ML IA" y el botón de menú. |
| RF-18 | `/` a 375 px | Pulsar ☰. | Se abre un panel con las ocho entradas en orden. |
| RF-19 | Panel abierto | Mirar el final del panel. | El selector ES/EN está al final. |
| RF-20 | Panel abierto | Pulsar "Torneos". | Se navega a `/tournaments` y el panel se cierra. |
| RF-21 | Panel abierto | Pulsar la zona oscura de la izquierda; volver a abrir y pulsar Escape. | El panel se cierra las dos veces. |
| RF-22 | Panel abierto | Intentar hacer scroll de la página de detrás. | La página de detrás no se mueve. |
| RF-23 | Panel abierto a 375 px | Ensanchar la ventana a 1024 px o más. | El panel se cierra y aparece la fila. |

## 2.4 Entrada activa, direcciones y navegador

| RF | Vista | Acción | Resultado esperado |
|---|---|---|---|
| RF-24 | `/players` | Mirar el menú. | "Jugadores" está subrayado. |
| RF-25 | `/no-existe` | Mirar el menú. | Ninguna entrada está subrayada. |
| RF-26 | Menú | Pasar el ratón por cada entrada y mirar la barra de estado. | Cada sección tiene su dirección: `/matches`, `/teams`, `/players`, `/tournaments`, `/standings`, `/news`, `/ml-models`. |
| RF-27 | Barra de direcciones | Escribir `localhost:5173/standings` y pulsar Intro; después recargar (⌘R). | Se abre "Posiciones" las dos veces. |
| RF-28 | Navegar Inicio → Equipos → Noticias | Pulsar Atrás y luego Adelante del navegador. | Se muestran Equipos y luego Noticias. |
| RF-29 | `/teams` a 375 px, con el panel abierto | Pulsar Atrás del navegador. | Se vuelve a la página anterior y el panel queda cerrado. |
| RF-30 | `/players` | Mirar la pestaña del navegador. | "Jugadores · Retake" ("Players · Retake" en inglés). |
| RF-31 | `/` | Mirar la pestaña. | Solo "Retake". |

## 2.5 Distribución de la página de inicio

| RF | Vista | Acción | Resultado esperado |
|---|---|---|---|
| RF-32 | `/` | Mirar debajo del menú. | El primer bloque es el spotlight. |
| RF-33 | `/` a 1440 px | Mirar la primera fila. | Noticias está a la derecha del spotlight. |
| RF-34 | `/` a 1440 px | Comparar anchos. | El spotlight ocupa unos dos tercios y noticias un tercio. |
| RF-35 | `/` a 1440 px | Mirar la segunda fila. | "Próximos partidos" ocupa todo el ancho, debajo de los dos. |
| RF-36 | `/` a 1023 px | Mirar la página. | Una columna: spotlight, noticias y próximos partidos. |

## 2.6 Secciones y bloques sin contenido

| RF | Vista | Acción | Resultado esperado |
|---|---|---|---|
| RF-37 | `/matches`, `/teams`, `/players`, `/tournaments`, `/standings`, `/news`, `/ml-models` | Abrir cada una. | Nombre de la sección y aviso "Próximamente". |
| RF-38 | `/` | Mirar la cinta y los tres huecos. | Cada uno muestra su nombre y "Próximamente". |
| RF-39 | `/` | Recargar y observar. | En los huecos no aparece ningún esqueleto de carga ni error. |

## 2.7 Carga, errores y conexión (en `/dev/block-demo`)

| RF | Vista | Acción | Resultado esperado |
|---|---|---|---|
| RF-40 | Demostración, escenario "Carga correcta" | Pulsar "Reiniciar bloque". | Durante 1 s se ve un esqueleto gris. |
| RF-41 | Escenario "Fallo de carga" | Esperar 1 s. | Aviso de error y botón "Reintentar". |
| RF-42 | Escenario "Carga que no termina" | Esperar 15 s. | A los 15 s el esqueleto se sustituye por el aviso de error. |
| RF-43 | Escenario "Datos tardíos" | Esperar 20 s. | A los 15 s sale el error; a los 20 s el partido de ejemplo sustituye al aviso. |
| RF-44 | Escenario "Fallo de carga", en error | Pulsar "Reintentar". | Vuelve el esqueleto y el contador "Intentos de carga iniciados" sube en 1. |
| RF-45 | Mismo escenario | Repetir "Reintentar" muchas veces. | Siempre se puede reintentar. |
| RF-46 | Mismo escenario, en error | Hacer doble clic rápido en "Reintentar". | El contador sube solo 1. |
| RF-47 | Escenario "Carga correcta" | Esperar 1 s. | Aparece el partido sin ningún mensaje de "éxito". |
| RF-48 | Escenario "Fallo de carga", en error | Usar el menú. | El menú funciona con normalidad. |
| RF-49 | Escenario "Fallo de carga", en error | Cambiar el ancho de 1280 a 375 px (o girar el dispositivo). | El bloque sigue en error y el contador no cambia. |
| RF-50 | Demostración | Network → *Offline*. | Aparece el aviso "Sin conexión" bajo el menú. |
| RF-51 | Escenario "Carga correcta" ya cargado | Network → *Offline*. | El partido sigue visible. |
| RF-52 | Sin conexión | Network → *No throttling*. | El aviso "Sin conexión" desaparece. |
| RF-53 | Sin conexión y escenario "Fallo de carga" en error | Volver a conectar. | El bloque reintenta solo: el contador sube en 1. |

## 2.8 Dirección inexistente

| RF | Vista | Acción | Resultado esperado |
|---|---|---|---|
| RF-54 | `/esto/no/existe` | Abrir la dirección. | "Página no encontrada", sin mostrar la dirección escrita. |
| RF-55 | Misma página | Pulsar "Volver a Inicio". | Lleva a Inicio. |

## 2.9 Pie de página

| RF | Vista | Acción | Resultado esperado |
|---|---|---|---|
| RF-56 | Cualquier página | Mirar el pie. | Aparece "Retake". |
| RF-57 | Cualquier página | Mirar el pie. | "Proyecto escolar sin afiliación oficial con la Call of Duty League." |
| RF-58 | Cualquier página | Mirar el pie. | "Temporada 2026" ("2026 season" en inglés). Es un valor provisional hasta la spec 003. |

## 2.10 Idioma

| RF | Vista | Acción | Resultado esperado |
|---|---|---|---|
| RF-59 | Cualquier página, a 1440 px y a 375 px (panel) | Buscar el selector. | Botones ES y EN; el activo aparece relleno. |
| RF-60 | Primera visita (borrar `retake.locale`) | En Chrome → Ajustes → Idiomas, poner inglés el primero y recargar. | La interfaz sale en inglés. |
| RF-61 | Primera visita | Poner "Español (México)" el primero y recargar. | La interfaz sale en español. |
| RF-62 | Primera visita | Poner solo alemán y recargar. | La interfaz sale en español. |
| RF-63 | `/players` | Pulsar EN. | Menú, avisos, pie y título pasan a inglés. |
| RF-64 | `/players` con scroll, o panel abierto a 375 px | Pulsar EN. | Se mantienen la página, el scroll y el panel abierto. |
| RF-65 | Tras elegir EN | Cerrar la pestaña y volver a abrir Retake. | Sale en inglés. |
| RF-66 | Tras elegir EN | Comprobar en Application → Local storage. | `retake.locale = en`, sin fecha de caducidad. |
| RF-67 | Con EN elegido | Poner español primero en Chrome y recargar. | Sigue en inglés. |
| RF-68 | Dos pestañas de Retake | En la segunda elegir el otro idioma. | La primera no cambia hasta recargarla. |
| RF-69 | Local storage | Cambiar `retake.locale` a `xx` y recargar. | Se aplica la regla de primera visita. |
| RF-70 | — | Revisar las claves `league.*` de `src/i18n/dictionaries/es.js` y `en.js`. | Existen las etiquetas de la spec 002 aprobada en los dos idiomas: las cinco fases (semana, grupo, winners bracket, losers bracket y gran final, sin "final") y las etiquetas `Por definir`, "Ganador de…", "Perdedor de…", `No jugado`, `Corregido`, `Agente libre` y el aviso de tabla no disponible. No hay traducción para `DQ`, `SMG` ni `AR`. Se verán en pantalla cuando las usen las specs de contenido. |
| RF-71 | Demostración, escenario "Carga correcta" | Cambiar de idioma. | "21 de septiembre de 2026 a las 18:30" pasa a "September 21, 2026 at 6:30 PM". |
| RF-72 | Demostración, partido cargado | Cambiar de idioma. | "FaZe VGS", "OpTic Texas", "Major 2 Qualifiers", "Hardpoint" y "Vault" no cambian. |

## 2.11 Accesibilidad

| RF | Vista | Acción | Resultado esperado |
|---|---|---|---|
| RF-73 | Todas las rutas | Ejecutar `npm run test:e2e`; opcionalmente, Lighthouse → Accesibilidad. | Sin incumplimientos de WCAG 2.2 AA. |
| RF-74 | Todas las rutas | Ejecutar `npm test`. La prueba de contraste la cubre. | Todas las parejas de color llegan a 4,5:1. |
| RF-75 | `/` | Pasar el ratón por entradas, logo, ES/EN, ☰ y "Reintentar". | Cada elemento cambia de color o de borde. |
| RF-76 | `/` | Recorrer con Tab. | Cada elemento enfocado muestra un contorno amarillo. |
| RF-77 | `/` | Mantener pulsado el ratón sobre cada elemento. | Cambia su fondo o se hunde levemente. |
| RF-78 | `/` | Recorrer toda la página solo con Tab, Mayús+Tab e Intro. | Se llega a todo: "Saltar al contenido", logo, entradas, idioma, botón de menú y "Reintentar". |
| RF-79 | `/` con VoiceOver (⌘F5) | Recorrer la cabecera. | Cada elemento se anuncia con un nombre: "Abrir menú", "Español", "Reintentar: …". |
| RF-80 | `/players` con VoiceOver | Llegar a "Jugadores". | Se anuncia como página actual. |
| RF-81 | `/` | Zoom del navegador al 200 % (⌘+). | Todo sigue visible y usable, sin scroll horizontal; el menú pasa a ☰. |
| RF-82 | Panel abierto a 375 px | Pulsar Tab muchas veces. | El foco no sale del panel. |
| RF-83 | Panel abierto | Pulsar Escape. | El foco vuelve al botón ☰. |

## 2.12 Animaciones

| RF | Vista | Acción | Resultado esperado |
|---|---|---|---|
| RF-84 | `/` a 375 px | Abrir y cerrar el panel. | Entra y sale deslizándose desde la derecha. |
| RF-85 | `/` | Cambiar de sección. | El contenido nuevo aparece con un fundido breve. |
| RF-86 | `/` | Pasar el ratón por ☰, ES/EN o "Reintentar". | El botón crece ligeramente. |
| RF-87 | — | Observar todas las animaciones. | Ninguna dura más de 300 ms. |
| RF-88 | macOS → Accesibilidad → Pantalla → **Reducir movimiento** | Repetir RF-84 a RF-86. | No hay deslizamiento, fundido ni crecimiento. |

## 2.13 Bloque de demostración

| RF | Vista | Acción | Resultado esperado |
|---|---|---|---|
| RF-89 | `npm run dev` → `/dev/block-demo` | Abrir la dirección. | Página "Demostración de bloque" con un bloque de prueba. |
| RF-90 | Demostración | Hacer las pruebas de §2.7. | El bloque cumple todas las reglas. |
| RF-91 | Demostración | Elegir "Carga que no termina". | El error aparece a los 15 s. |
| RF-92 | Demostración | Elegir "Fallo de carga". | El error aparece a 1 s. |
| RF-93 | Demostración | Elegir "Datos tardíos". | Los datos llegan después del error. |
| RF-94 | Demostración | Mirar el menú. | No hay ninguna entrada que lleve a la demostración. |
| RF-95 | `npm run build && npm run preview` → `/dev/block-demo` | Abrir la dirección. | "Página no encontrada". |

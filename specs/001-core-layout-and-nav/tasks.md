# Tasks: Estructura Base y Navegación

- **Spec**: [`spec.md`](spec.md) (`Aprobado`, 2026-09-22)
- **Plan**: [`plan.md`](plan.md) (`Aprobado`, 2026-09-22)
- **Fecha**: `2026-09-22`
- **Estado**: `Aprobado` (aprobado por Hugo el 2026-09-22). Implementación completa: T-001 a T-083. Cierre aprobado por Hugo el 2026-09-22.

Checklist de tareas atómicas, en orden de ejecución. Cada tarea indica los requisitos que cubre (**RF**), de qué tareas depende (**Dep.**) y cuándo se considera terminada (**Hecho cuando**).

## Reglas de ejecución

1. **Orden:** las tareas se hacen en orden. Una tarea no empieza hasta que sus dependencias estén marcadas.
2. **Alcance cerrado:** solo se implementa lo que dice cada tarea (constitución §1.2). Si aparece un imprevisto, se detiene el trabajo y se consulta a Hugo antes de seguir; si cambia algo, se actualizan la spec y el plan (constitución §1.3).
3. **Cierre de fase:** cada fase termina con una tarea de cierre, que exige:
   - todas las pruebas automáticas en verde;
   - la guía de verificación manual de la fase entregada a Hugo (constitución §5.1);
   - un mensaje de commit sugerido. El commit lo hace Hugo: el agente no ejecuta comandos de git que modifiquen el repositorio (constitución §8).
4. **Documentación del código:** los contratos se documentan con comentarios JSDoc en español (plan D-17). Los nombres de código van en inglés (constitución §7).

## Nota de ejecución (2026-09-22)

Hugo pidió implementar la spec completa de una vez, así que las guías manuales de cada fase se entregaron **consolidadas** en [`verification-guide.md`](verification-guide.md) y se sugiere un **único commit** al final. Los ajustes surgidos durante la implementación están en el plan, §10.

## Dependencias externas

| Qué | Lo aporta | Afecta a | Mientras tanto |
|---|---|---|---|
| Archivo del logo de Retake (SVG o PNG) | Hugo | T-029 | La tarea se puede completar: sin imagen se aplica RF-13 y se muestra el texto "Retake". Cuando llegue el archivo, solo hay que añadirlo. |

---

## F0 — Base del proyecto

- [x] **T-001** Crear en la raíz del repositorio un proyecto Vite + React en JavaScript, gestionado con npm.
  - **RF:** —
  - **Dep.:** —
  - **Hecho cuando:** `npm run dev` sirve la página de ejemplo de Vite sin errores en consola.
- [x] **T-002** Borrar la plantilla de ejemplo de Vite y crear las carpetas de `src/` del plan §1: `app`, `config`, `layout`, `navigation`, `pages`, `blocks`, `connection`, `i18n`, `motion` y `shared`.
  - **RF:** —
  - **Dep.:** T-001
  - **Hecho cuando:** la aplicación arranca y muestra una página vacía, sin errores.
- [x] **T-003** Instalar y configurar Tailwind CSS.
  - **RF:** —
  - **Dep.:** T-002
  - **Hecho cuando:** una clase de Tailwind aplicada a `App` se ve en el navegador.
- [x] **T-004** Definir en un módulo compartido (lo leen Tailwind y las pruebas) las variables de diseño del tema oscuro: fondo, superficie, texto principal, texto secundario, acento, color exclusivo de Modelos de ML, foco y error. El documento usa siempre el fondo oscuro.
  - **RF:** RF-5
  - **Dep.:** T-003
  - **Hecho cuando:** la página se ve oscura aunque el sistema operativo esté en modo claro.
- [x] **T-005** Instalar Anime.js, React Router, i18next y react-i18next.
  - **RF:** —
  - **Dep.:** T-002
  - **Hecho cuando:** las cuatro librerías aparecen en `package.json` y la aplicación sigue arrancando.
- [x] **T-006** Configurar Vitest y Testing Library con un navegador simulado, y añadir el script `npm test`.
  - **RF:** —
  - **Dep.:** T-002
  - **Hecho cuando:** una prueba de humo pasa con `npm test`.
- [x] **T-007** Configurar Playwright y axe con dos entornos, desarrollo y versión de producción, y añadir el script `npm run test:e2e`.
  - **RF:** —
  - **Dep.:** T-002
  - **Hecho cuando:** una prueba de humo pasa en los dos entornos.
- [x] **T-008** Escribir una prueba unitaria que calcule el contraste de cada pareja texto/fondo de las variables de diseño, incluido el texto de Modelos de ML sobre su color exclusivo. Ajustar los colores hasta que todas las parejas lleguen a 4,5:1.
  - **RF:** RF-74
  - **Dep.:** T-004, T-006
  - **Hecho cuando:** la prueba pasa y ninguna pareja baja de 4,5:1.
- [x] **T-009** Crear `config/layoutConstants` con el umbral de 1024 px, la espera máxima de 15 000 ms, la duración máxima de animación de 300 ms y el ancho mínimo de 320 px, documentados con JSDoc.
  - **RF:** RF-4, RF-7, RF-16, RF-42, RF-87
  - **Dep.:** T-002
  - **Hecho cuando:** las constantes existen y están documentadas.
- [x] **T-010 · Cierre F0**
  - **Dep.:** T-001 a T-009
  - **Hecho cuando:** `npm test` y `npm run test:e2e` están en verde, se ha entregado la guía manual (arrancar el proyecto y ver el fondo oscuro) y se ha sugerido el commit.

---

## F1 — Idioma

- [x] **T-011** Pruebas unitarias e implementación de `resolveInitialLocale`, con estos casos:
  - `fr, en` → `en`
  - `es-MX` → `es`
  - `en-GB` → `en`
  - `de` → `es`
  - lista vacía → `es`
  - **RF:** RF-60, RF-61, RF-62
  - **Dep.:** T-006
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-012** Pruebas unitarias e implementación de `localeStorage`: lee y guarda la clave `retake.locale`. Si el valor no es `es` ni `en`, o el almacenamiento no está disponible, devuelve "sin elección" sin lanzar errores.
  - **RF:** RF-65, RF-66, RF-69
  - **Dep.:** T-006
  - **Hecho cuando:** las pruebas cubren un valor válido, un valor manipulado y un almacenamiento inaccesible.
- [x] **T-013** Pruebas unitarias e implementación de la regla de idioma inicial: si hay una elección guardada válida, manda sobre el navegador; si no, se aplica `resolveInitialLocale`.
  - **RF:** RF-65, RF-67, RF-69
  - **Dep.:** T-011, T-012
  - **Hecho cuando:** las pruebas pasan, incluido el caso "guardado `en` y navegador `es`" → `en`.
- [x] **T-014** Crear los diccionarios `es` y `en` con todos los textos del marco:
  - los nombres de las ocho secciones y de los cuatro bloques;
  - "Próximamente", "Página no encontrada", el enlace a Inicio, el aviso de error, "Reintentar" y "Sin conexión";
  - la etiqueta "IA" ("AI" en inglés, según RF-63);
  - el aviso del pie, los títulos de pestaña, el selector de idioma y los nombres accesibles de los elementos interactivos.
  - **RF:** RF-63
  - **Dep.:** T-005
  - **Hecho cuando:** los dos diccionarios contienen todas las claves.
- [x] **T-015** Añadir a los diccionarios las etiquetas de estado y de fase de la spec 002: `programado`, `en vivo`, `finalizado`, `No disponible`, `Sin rol`, "Estadísticas pendientes", semana, grupo, winners bracket, losers bracket y final.
  - **RF:** RF-70
  - **Dep.:** T-014
  - **Hecho cuando:** todas las etiquetas existen en `es` y `en`.
- [x] **T-016** Prueba unitaria de completitud de los diccionarios: toda clave existe en los dos idiomas y ninguna está vacía.
  - **RF:** RF-63, RF-70
  - **Dep.:** T-015
  - **Hecho cuando:** la prueba pasa, y falla si se borra una clave de un solo idioma.
- [x] **T-017** Configurar react-i18next con los diccionarios, **sin** su detector de idioma y sin sincronizar pestañas. El idioma inicial sale de la regla de T-013.
  - **RF:** RF-60, RF-68
  - **Dep.:** T-013, T-016
  - **Hecho cuando:** la aplicación arranca en el idioma que devuelve la regla.
- [x] **T-018** `LocaleProvider`: expone el idioma activo y la acción de cambiarlo. Al cambiar, guarda la elección, actualiza el atributo de idioma del documento y traduce los textos sin volver a montar la página.
  - **RF:** RF-63, RF-64, RF-65
  - **Dep.:** T-017
  - **Hecho cuando:** una prueba de componente comprueba que un componente hijo conserva su estado interno al cambiar de idioma.
- [x] **T-019** Pruebas unitarias e implementación de los formateadores de fecha y hora por idioma, con la API de internacionalización nativa del navegador.
  - **RF:** RF-71
  - **Dep.:** T-018
  - **Hecho cuando:** una misma fecha de prueba sale con formato español en `es` y con formato inglés en `en`.
- [x] **T-020** `LanguageSwitcher`: dos botones, ES y EN. El activo se indica como pulsado y cada opción tiene su nombre accesible en su propio idioma.
  - **RF:** RF-59, RF-63, RF-79
  - **Dep.:** T-018
  - **Hecho cuando:** una prueba de componente comprueba el cambio de idioma y los nombres accesibles.
- [x] **T-021 · Cierre F1**
  - **Dep.:** T-011 a T-020
  - **Hecho cuando:** las pruebas están en verde, se ha entregado la guía manual (cambiar el idioma del navegador y recargar) y se ha sugerido el commit.

---

## F2 — Marco y rutas

- [x] **T-022** Pruebas unitarias e implementación de `sectionsRegistry` con las ocho secciones del plan §3.1.
  - **RF:** RF-6, RF-8, RF-26, RF-37
  - **Dep.:** T-014
  - **Hecho cuando:** las pruebas confirman el orden de RF-6, que solo `mlModels` está destacada y que solo `home` tiene contenido.
- [x] **T-023** Pruebas unitarias e implementación de `homeBlocksRegistry` con los cuatro bloques, todos sin contenido.
  - **RF:** RF-38, RF-39
  - **Dep.:** T-014
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-024** `AppShell`: de arriba abajo, franja de la cinta, cabecera, espacio para el aviso de conexión, zona de contenido y pie. Nada queda fijo al hacer scroll.
  - **RF:** RF-1, RF-3
  - **Dep.:** T-004
  - **Hecho cuando:** una prueba de componente verifica el orden.
- [x] **T-025** `ComingSoonPage`: nombre de la sección y aviso "Próximamente".
  - **RF:** RF-37
  - **Dep.:** T-014
  - **Hecho cuando:** una prueba de componente pasa en los dos idiomas.
- [x] **T-026** `NotFoundPage`: aviso "Página no encontrada" y enlace a Inicio. La página **no** muestra la dirección escrita por el usuario.
  - **RF:** RF-54, RF-55
  - **Dep.:** T-014
  - **Hecho cuando:** una prueba de componente pasa.
- [x] **T-027** Tabla de rutas generada desde `sectionsRegistry`, toda dentro de `AppShell`:
  - `/` → Inicio, que de momento es una página vacía hasta T-050;
  - secciones sin contenido → `ComingSoonPage`;
  - cualquier otra dirección → `NotFoundPage`.
  - **RF:** RF-1, RF-26, RF-27, RF-54
  - **Dep.:** T-022, T-024, T-025, T-026
  - **Hecho cuando:** las ocho direcciones y una dirección inventada muestran la página correcta.
- [x] **T-028** `usePageTitle`: el título es "<página> · Retake", o solo "Retake" en Inicio, y se actualiza al cambiar de idioma.
  - **RF:** RF-30, RF-31
  - **Dep.:** T-018, T-027
  - **Hecho cuando:** una prueba de componente comprueba el título en Inicio, en una sección y en la 404, en los dos idiomas.
- [x] **T-029** `Logo`: imagen enlazada a Inicio, con nombre accesible. Si la imagen falla, muestra el texto "Retake" y conserva el enlace.
  - **RF:** RF-11, RF-12, RF-13, RF-79
  - **Dep.:** T-027
  - **Hecho cuando:** una prueba de componente simula el fallo de la imagen y ve el texto enlazado.
- [x] **T-030** Crear el contrato `SeasonInfo` con un valor provisional de `2026` en configuración. El comentario JSDoc indica que es provisional hasta la spec 003.
  - **RF:** RF-58
  - **Dep.:** T-002
  - **Hecho cuando:** el valor está disponible para el pie.
- [x] **T-031** `SiteFooter`: nombre Retake, aviso de proyecto escolar sin afiliación y año de `SeasonInfo`.
  - **RF:** RF-56, RF-57, RF-58
  - **Dep.:** T-014, T-030
  - **Hecho cuando:** una prueba de componente pasa en los dos idiomas.
- [x] **T-032** Prueba de extremo a extremo del marco:
  - cada dirección de sección se abre directamente y al recargar;
  - una dirección inventada muestra la 404;
  - la 404 y "Próximamente" tienen el marco completo.
  - **RF:** RF-1, RF-27, RF-54
  - **Dep.:** T-027 a T-031
  - **Hecho cuando:** la prueba pasa en los dos entornos.
- [x] **T-033 · Cierre F2**
  - **Dep.:** T-022 a T-032
  - **Hecho cuando:** las pruebas están en verde, se ha entregado la guía manual (abrir cada sección, una dirección inventada y el pie) y se ha sugerido el commit.

---

## F3 — Menú

- [x] **T-034** Pruebas unitarias e implementación de `useActiveSection`. La sección activa se calcula a partir de la **ruta que ha coincidido**, no del texto de la dirección. Casos:
  - `/` → `home`
  - `/players` → `players`
  - una subpágina definida → su sección madre
  - dirección sin ruta (incluida `/players/xyz` mientras no exista esa subpágina) → ninguna
  - **RF:** RF-24, RF-25
  - **Dep.:** T-027
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-035** `NavItem`: enlace a la sección, subrayado e indicado como página actual a los lectores de pantalla cuando está activo. Tiene dos variantes, fila y panel, y avisa al pulsarse.
  - **RF:** RF-14, RF-24, RF-80
  - **Dep.:** T-034
  - **Hecho cuando:** una prueba de componente pasa.
- [x] **T-036** Tratamiento destacado de Modelos de ML en `NavItem`: fondo exclusivo, un icono SVG propio (sin librería de iconos) y la etiqueta "IA".
  - **RF:** RF-8, RF-9, RF-10
  - **Dep.:** T-035
  - **Hecho cuando:** una prueba de componente comprueba que solo esa entrada lleva el fondo, el icono y la etiqueta.
- [x] **T-037** `MainNav` dentro de `SiteHeader`: desde 1024 px muestra en una sola fila el logo, las ocho entradas y el selector de idioma. Por debajo se oculta solo con estilos.
  - **RF:** RF-6, RF-7, RF-11, RF-59
  - **Dep.:** T-020, T-029, T-036
  - **Hecho cuando:** se ve completo a 1440 px.
- [x] **T-038** `useScrollTopOnSameSection`: al pulsar la entrada de la sección actual, se vuelve al principio de la página. El desplazamiento es instantáneo si el usuario pide reducir movimiento.
  - **RF:** RF-15, RF-88
  - **Dep.:** T-035
  - **Hecho cuando:** una prueba de componente pasa.
- [x] **T-039** Prueba de extremo a extremo del menú a 1440 px y a 1024 px, en `es` y en `en`: orden de las entradas, navegación, entrada activa y ausencia de desbordamiento o scroll horizontal a 1024 px en inglés (riesgo del plan §8).
  - **RF:** RF-4, RF-6, RF-7, RF-14, RF-24
  - **Dep.:** T-037, T-038
  - **Hecho cuando:** la prueba pasa. Si no cabe a 1024 px, se detiene el trabajo y se consulta a Hugo (constitución §1.4).
- [x] **T-040 · Cierre F3**
  - **Dep.:** T-034 a T-039
  - **Hecho cuando:** las pruebas están en verde, se ha entregado la guía manual (navegar por el menú en escritorio y comprobar el subrayado y el destacado de ML) y se ha sugerido el commit.

---

## F4 — Menú plegado

- [x] **T-041** Pruebas unitarias e implementación de `useNavPanelState`: abre y cierra el panel, y lo cierra al cambiar de dirección, al pulsar Escape y al pasar a 1024 px o más.
  - **RF:** RF-21, RF-23, RF-28, RF-29
  - **Dep.:** T-009
  - **Hecho cuando:** las pruebas cubren los tres motivos de cierre.
- [x] **T-042** `CompactNavBar`: por debajo de 1024 px muestra el logo, el acceso destacado a Modelos de ML y el botón de menú. El botón tiene nombre accesible e indica si el panel está abierto y qué panel controla.
  - **RF:** RF-16, RF-17, RF-79
  - **Dep.:** T-036, T-041
  - **Hecho cuando:** se ve a 375 px y una prueba de componente comprueba los atributos accesibles.
- [x] **T-043** `MobileNavPanel`: las ocho entradas en orden, en la variante de panel, y el selector de idioma al final. Al pulsar cualquier entrada, incluida la de la sección actual, el panel se cierra.
  - **RF:** RF-6, RF-18, RF-19, RF-20
  - **Dep.:** T-042
  - **Hecho cuando:** una prueba de componente pasa.
- [x] **T-044** Capa de fondo del panel: al pulsarla, el panel se cierra.
  - **RF:** RF-21
  - **Dep.:** T-043
  - **Hecho cuando:** una prueba de componente pasa.
- [x] **T-045** Bloquear el scroll de la página mientras el panel está abierto y restaurarlo al cerrar.
  - **RF:** RF-22
  - **Dep.:** T-043
  - **Hecho cuando:** la página no se desplaza con el panel abierto y sí al cerrarlo.
- [x] **T-046** `useFocusContainment`: al abrir el panel, vuelve inerte el resto de la página y lleva el foco al panel. Al cerrarlo, devuelve el foco al botón de menú.
  - **RF:** RF-82, RF-83
  - **Dep.:** T-043
  - **Hecho cuando:** una prueba de componente comprueba que el foco no sale del panel y vuelve al botón.
- [x] **T-047** Prueba de extremo a extremo a 375 px:
  - abrir el panel, navegar, Escape y pulsar fuera;
  - redimensionar a 1024 px con el panel abierto;
  - Atrás del navegador con el panel abierto;
  - Tab no sale del panel.
  - **RF:** RF-16 a RF-23, RF-28, RF-29, RF-82, RF-83
  - **Dep.:** T-041 a T-046
  - **Hecho cuando:** la prueba pasa.
- [x] **T-048 · Cierre F4**
  - **Dep.:** T-041 a T-047
  - **Hecho cuando:** las pruebas están en verde, se ha entregado la guía manual (móvil: abrir y cerrar el panel de cada forma y recorrerlo con teclado) y se ha sugerido el commit.

---

## F5 — Inicio y huecos

- [x] **T-049** `BlockSlot` y `ComingSoonBlock`: un bloque sin contenido muestra su nombre y "Próximamente" sin poner en marcha ninguna carga.
  - **RF:** RF-38, RF-39
  - **Dep.:** T-023
  - **Hecho cuando:** una prueba de componente comprueba que la función de carga no se llama nunca.
- [x] **T-050** `HomePage`: desde 1024 px, spotlight en 2/3, noticias en 1/3 y cuadrícula debajo a todo el ancho. Por debajo de 1024 px, una columna con spotlight, noticias y cuadrícula. Todo solo con estilos (plan D-1).
  - **RF:** RF-32 a RF-36, RF-49
  - **Dep.:** T-049
  - **Hecho cuando:** la distribución se ve correcta a 1440 px y a 375 px.
- [x] **T-051** `ScoreTickerSlot`: franja a todo el ancho encima del menú, con el `BlockSlot` de la cinta.
  - **RF:** RF-2, RF-38
  - **Dep.:** T-049
  - **Hecho cuando:** aparece en todas las páginas, encima del menú.
- [x] **T-052** Prueba de extremo a extremo del inicio:
  - a 1440 px, noticias a la derecha, anchos en proporción 2:1 y cuadrícula debajo;
  - a 1023 px, orden apilado;
  - la cinta está encima del menú en todas las rutas.
  - **RF:** RF-2, RF-32 a RF-36
  - **Dep.:** T-050, T-051
  - **Hecho cuando:** la prueba pasa.
- [x] **T-053 · Cierre F5**
  - **Dep.:** T-049 a T-052
  - **Hecho cuando:** las pruebas están en verde, se ha entregado la guía manual (inicio en escritorio y en móvil) y se ha sugerido el commit.

---

## F6 — Carga y conexión

- [x] **T-054** Pruebas unitarias e implementación de `ConnectionProvider`: expone el estado de conexión y avisa cuando la red vuelve, simulando los eventos de conexión y desconexión.
  - **RF:** RF-50, RF-52, RF-53
  - **Dep.:** T-006
  - **Hecho cuando:** las pruebas pasan.
- [x] **T-055** `OfflineBanner` en `AppShell`: el aviso "Sin conexión" aparece mientras no hay red y desaparece al volver.
  - **RF:** RF-50, RF-52
  - **Dep.:** T-054, T-024
  - **Hecho cuando:** una prueba de componente pasa.
- [x] **T-056** Escribir las pruebas unitarias de `useBlockLoader`, **antes de implementarlo**, con temporizadores simulados: una prueba por cada fila de la tabla de transiciones del plan §3.4, más "datos tardíos tras `ready` se descartan".
  - **RF:** RF-40 a RF-47, RF-49, RF-51, RF-53
  - **Dep.:** T-006, T-009
  - **Hecho cuando:** las pruebas existen y fallan por falta de implementación.
- [x] **T-057** Implementar `useBlockLoader`: 15 s por intento sin cancelar la petición, aprovechamiento de datos tardíos, un único intento en curso y reintento al volver la red (plan D-4 a D-6).
  - **RF:** RF-40 a RF-47, RF-53
  - **Dep.:** T-054, T-056
  - **Hecho cuando:** todas las pruebas de T-056 pasan.
- [x] **T-058** `BlockSkeleton`: un esqueleto genérico que admite un parámetro de forma y se anuncia como "cargando" a los lectores de pantalla.
  - **RF:** RF-40
  - **Dep.:** T-004
  - **Hecho cuando:** una prueba de componente pasa.
- [x] **T-059** `BlockError`: aviso de error y botón "Reintentar", cuyo nombre accesible incluye el nombre del bloque.
  - **RF:** RF-41, RF-44, RF-79
  - **Dep.:** T-014
  - **Hecho cuando:** una prueba de componente pasa.
- [x] **T-060** `AsyncBlock`: une el cargador con el esqueleto, el error o el contenido. Cuando la carga tiene éxito, no muestra ningún aviso adicional. `BlockSlot` delega en `AsyncBlock` cuando el bloque tiene contenido.
  - **RF:** RF-40, RF-41, RF-47, RF-48
  - **Dep.:** T-049, T-057 a T-059
  - **Hecho cuando:** una prueba de componente comprueba que dos bloques, uno en error y otro cargado, son independientes.
- [x] **T-061** Pruebas unitarias e implementación de los escenarios de demostración `ok`, `fail`, `hang` y `late` (plan §3.5), como funciones de carga falsas. El contenido de prueba incluye nombres propios de la liga (ej. "FaZe VGS") para comprobar RF-72.
  - **RF:** RF-72, RF-91, RF-92, RF-93
  - **Dep.:** T-006
  - **Hecho cuando:** las pruebas pasan con temporizadores simulados.
- [x] **T-062** `BlockDemoPage` en `/dev/block-demo`:
  - un bloque de prueba con un control para elegir el escenario y otro para reiniciar;
  - la ruta solo se registra y se carga en modo desarrollo (plan D-13);
  - no está en el registro de secciones.
  - **RF:** RF-89, RF-90, RF-94
  - **Dep.:** T-027, T-060, T-061
  - **Hecho cuando:** la página funciona en desarrollo y no aparece en el menú.
- [x] **T-063** Prueba de extremo a extremo en la **versión de producción**: `/dev/block-demo` muestra la 404 y el paquete generado no contiene código de la página de demostración.
  - **RF:** RF-95
  - **Dep.:** T-062
  - **Hecho cuando:** la prueba pasa.
- [x] **T-064** Prueba de extremo a extremo en **desarrollo** con la página de demostración, usando el reloj simulado de Playwright:
  - los cuatro escenarios;
  - varias pulsaciones de "Reintentar" provocan una sola carga (se cuentan las llamadas);
  - sin red: aparece el aviso, se conserva el contenido y, al volver la red, el bloque en error reintenta;
  - un bloque en error no afecta al menú;
  - al redimensionar se conserva el estado;
  - los nombres propios no se traducen al pasar a `en`.
  - **RF:** RF-40 a RF-53, RF-72, RF-89 a RF-93
  - **Dep.:** T-055, T-062
  - **Hecho cuando:** la prueba pasa.
- [x] **T-065 · Cierre F6**
  - **Dep.:** T-054 a T-064
  - **Hecho cuando:** las pruebas están en verde, se ha entregado la guía manual (página de demostración: cada escenario y corte de red desde las herramientas del navegador) y se ha sugerido el commit.

---

## F7 — Movimiento

- [x] **T-066** `useReducedMotion` y `MotionProvider`: detectan la preferencia de reducir movimiento y reaccionan si cambia.
  - **RF:** RF-88
  - **Dep.:** T-006
  - **Hecho cuando:** una prueba unitaria simula el cambio de preferencia.
- [x] **T-067** `motionPresets` con duraciones y curvas comunes.
  - **RF:** RF-87
  - **Dep.:** T-009
  - **Hecho cuando:** una prueba unitaria comprueba que ninguna duración supera la constante de 300 ms.
- [x] **T-068** `useSlideAnimation`: el panel entra y sale deslizándose con Anime.js. Al cerrar, el panel se desmonta cuando termina la animación. Sin animación si se pide reducir movimiento.
  - **RF:** RF-84, RF-87, RF-88
  - **Dep.:** T-043, T-066, T-067
  - **Hecho cuando:** se ve el deslizamiento y el foco sigue volviendo al botón (RF-83).
- [x] **T-069** `PageTransition` en la zona de contenido al cambiar de dirección, sin interferir con el foco ni con el título de la pestaña.
  - **RF:** RF-85, RF-87, RF-88
  - **Dep.:** T-027, T-066, T-067
  - **Hecho cuando:** se ve la transición al navegar.
- [x] **T-070** `useHoverAnimation` aplicado a los botones del marco: botón de menú, selector de idioma y "Reintentar".
  - **RF:** RF-86, RF-87, RF-88
  - **Dep.:** T-066, T-067
  - **Hecho cuando:** los botones animan su hover.
- [x] **T-071** Prueba de extremo a extremo con reducir movimiento activado: el panel aparece y desaparece sin deslizamiento y el cambio de página es inmediato.
  - **RF:** RF-88
  - **Dep.:** T-068 a T-070
  - **Hecho cuando:** la prueba pasa.
- [x] **T-072 · Cierre F7**
  - **Dep.:** T-066 a T-071
  - **Hecho cuando:** las pruebas están en verde, se ha entregado la guía manual (ver las animaciones y activar reducir movimiento en el sistema) y se ha sugerido el commit.

---

## F8 — Accesibilidad y cierre

- [x] **T-073** Repasar los estados hover, focus y active de todos los elementos interactivos del marco: entradas, logo, botón de menú, selector, "Reintentar", enlace de la 404 y controles de la demostración.
  - **RF:** RF-75, RF-76, RF-77
  - **Dep.:** T-070
  - **Hecho cuando:** cada elemento muestra los tres estados de forma visible.
- [x] **T-074** Prueba de extremo a extremo con axe:
  - todas las rutas, incluidas la 404 y la demostración en desarrollo;
  - a 320 y 1440 px;
  - con el panel abierto y cerrado;
  - en `es` y en `en`;
  - con las reglas WCAG 2.0, 2.1 y 2.2 de nivel A y AA.
  - **RF:** RF-73, RF-74
  - **Dep.:** T-073
  - **Hecho cuando:** hay cero incumplimientos.
- [x] **T-075** Prueba de extremo a extremo de recorrido solo con teclado: Tab alcanza el logo, las entradas, el selector, el botón de menú y "Reintentar", y Enter los activa.
  - **RF:** RF-78, RF-79, RF-80
  - **Dep.:** T-073
  - **Hecho cuando:** la prueba pasa.
- [x] **T-076** Prueba de extremo a extremo de zoom al 200 %, simulado con una ventana de 640 px: todo visible y utilizable y sin scroll horizontal.
  - **RF:** RF-4, RF-81
  - **Dep.:** T-073
  - **Hecho cuando:** la prueba pasa.
- [x] **T-077** Prueba de extremo a extremo de idioma y tema:
  - navegador en `fr, en` → `en`, y en `de` → `es`;
  - al cambiar de idioma se conservan el scroll y el panel;
  - al recargar se recuerda la elección;
  - dos pestañas conservan cada una su idioma;
  - un valor manipulado (`xx`) aplica la regla de primera visita;
  - el tema sigue oscuro con el sistema en modo claro.
  - **RF:** RF-5, RF-59 a RF-69
  - **Dep.:** T-020, T-043
  - **Hecho cuando:** la prueba pasa.
- [x] **T-078** Prueba de extremo a extremo sin scroll horizontal a 320, 1023, 1024 y 1440 px, en todas las rutas y en los dos idiomas.
  - **RF:** RF-4
  - **Dep.:** T-052
  - **Hecho cuando:** la prueba pasa.
- [x] **T-079** Checklist de seguridad (plan §5, constitución §6):
  - no se inserta HTML sin escapar;
  - la 404 no refleja la dirección;
  - el idioma guardado se valida;
  - el paquete de producción no contiene la demostración;
  - no hay secretos en el código.
  - **RF:** —
  - **Dep.:** T-063, T-077
  - **Hecho cuando:** cada punto está revisado y anotado con su resultado.
- [x] **T-080** Redactar la guía de verificación manual completa de RF-1 a RF-95 (constitución §5.1) y entregársela a Hugo. Incluye el giro de un dispositivo real (RF-49) y la comprobación visual de los estados de T-073.
  - **RF:** RF-1 a RF-95
  - **Dep.:** T-073 a T-079
  - **Hecho cuando:** cada RF tiene su paso: vista, acción y resultado esperado.
- [x] **T-081** Hugo ejecuta la guía. Cada fallo encontrado se documenta con causa raíz, impacto y solución (constitución §5.2), y se corrige antes de continuar.
  - **RF:** RF-1 a RF-95
  - **Dep.:** T-080
  - **Hecho cuando:** Hugo confirma que todos los RF se cumplen.
- [x] **T-082** Sincronizar la spec y el plan con cualquier cambio surgido durante la implementación (constitución §1.3) y marcar los diez criterios de finalización de la spec.
  - **RF:** —
  - **Dep.:** T-081
  - **Hecho cuando:** la spec, el plan y el código coinciden, y los criterios están cumplidos.
- [x] **T-083 · Cierre F8 y de la spec 001**
  - **Dep.:** T-073 a T-082
  - **Hecho cuando:** todas las pruebas están en verde, se ha sugerido el commit final y Hugo aprueba el cierre de la spec 001.

---

## Trazabilidad RF → tareas

| RF | Tareas |
|---|---|
| RF-1 a RF-3 | T-024, T-027, T-032, T-051 |
| RF-4 | T-009, T-039, T-076, T-078 |
| RF-5 | T-004, T-077 |
| RF-6 a RF-10 | T-022, T-035 a T-037, T-039, T-043 |
| RF-11 a RF-15 | T-029, T-035, T-037, T-038 |
| RF-16 a RF-23 | T-041 a T-047 |
| RF-24, RF-25 | T-034, T-035 |
| RF-26, RF-27 | T-022, T-027, T-032 |
| RF-28, RF-29 | T-041, T-047 |
| RF-30, RF-31 | T-028 |
| RF-32 a RF-36 | T-050, T-052 |
| RF-37 | T-022, T-025, T-027 |
| RF-38, RF-39 | T-023, T-049, T-051 |
| RF-40 a RF-53 | T-054 a T-060, T-064 |
| RF-54, RF-55 | T-026, T-027, T-032 |
| RF-56 a RF-58 | T-030, T-031 |
| RF-59 a RF-69 | T-011 a T-013, T-017, T-018, T-020, T-077 |
| RF-70, RF-71 | T-015, T-016, T-019 |
| RF-72 | T-061, T-064 |
| RF-73, RF-74 | T-008, T-074 |
| RF-75 a RF-77 | T-073 |
| RF-78 a RF-80 | T-020, T-035, T-042, T-059, T-075 |
| RF-81 | T-076 |
| RF-82, RF-83 | T-046, T-047 |
| RF-84 a RF-88 | T-038, T-066 a T-071 |
| RF-89 a RF-95 | T-061 a T-064 |

# Spec: Obtención y Actualización de los Datos de la Liga

- **ID**: `003-league-data-sync`
- **Fecha**: `2026-09-23` (borrador, segunda ronda de pendientes y resolución de la revisión QA, el mismo día)
- **Estado**: `Aprobado` (aprobada por Hugo el 2026-09-23; revisión R-1 del mismo día, durante el plan; cambios C-15 a C-21 del mismo día: la Wiki entra por archivos CSV; cambios C-22 a C-27 del 2026-09-24: franquicias que la fuente ya no lista, equipos invitados, revisión de partidos finalizados, rosters de equipos ajenos a la CDL y registro al cambiar de modo)

> **Numeración:** tras la revisión QA, la spec se renumeró de principio a fin, porque aún no estaba aprobada y ninguna otra spec cita sus números. Las tablas del §5 usan ya los números nuevos.

---

## 1. Contexto y Propósito (Por Qué)

La spec 002 definió **qué** información de la liga existe en Retake y cómo se comporta. Hoy esa información sale de datos de prueba transcritos a mano, así que Retake no refleja lo que pasa en la liga. Esta spec define **cómo llega y se mantiene al día**, para que la cinta de marcadores, el spotlight, la cuadrícula de partidos y el resto de secciones muestren la liga real casi en directo.

Esta spec define:

- de qué fuentes llega la información y qué normas de buen uso respeta Retake al consultarlas;
- cada cuánto se consulta cada tipo de dato y con qué retraso aparece en una página ya abierta;
- cómo se reconoce el mismo partido, jugador o franquicia en fuentes distintas;
- qué pasa cuando una fuente falla, cambia de formato o deja de publicar algo;
- cómo sabe el usuario final cuándo cambiaron por última vez los datos que ve y cuándo pueden estar desactualizados;
- cómo se entera Hugo de los problemas y cómo fuerza una actualización, desde una página privada;
- el cambio automático de temporada y el año del pie de página.

Además, cierra tres deudas de specs anteriores:

- **Cambio de temporada.** La nota de RF-3 y la decisión C-8 de la 002 piden que sea automático.
- **Año del pie.** La decisión P-6 de la 001 lo dejó como valor manual "hasta la 003".
- **Pendientes del plan de la 002.** Enlazar las identidades de las distintas fuentes (ajuste I-15) y guardar copias propias de los logos.

### 1.1 Glosario

| Término | Significado en esta spec |
|---|---|
| **Fuente** | Cada una de las tres fuentes de RF-66 de la 002: BreakingPoint.gg, Call of Duty Esports Wiki (Fandom) y la web oficial de la CDL. |
| **Consulta** | Cada vez que Retake pide datos a una fuente. Una consulta **con éxito** es la que obtiene una respuesta que Retake entiende, al menos en parte. |
| **Registrar** | Que un dato nuevo o cambiado quede guardado en Retake y disponible para la web (mismo verbo que en la 002). |
| **Datos en vivo** | De un partido `en vivo`: su estado, su marcador (mapas ganados y marcador del mapa en curso, RF-36 y RF-37 de la 002) y, de cada mapa ya terminado de ese partido, su marcador final, su ganador y las estadísticas de sus jugadores. |
| **Resto de datos** | Cualquier otro dato de la temporada actual de la 002. Por ejemplo: calendario y horarios, eventos, fases, partidos finalizados, jugadores, rosters, franquicias, identidades, tabla de posiciones y correcciones. |
| **Archivos de la Wiki** | Archivos CSV con datos de la Wiki que el administrador prepara y actualiza fuera de Retake: el historial de campeonatos, los nombres y fechas de nacimiento de los jugadores y los rosters por temporada con el país (cambio C-15). |
| **Historial** | El historial de campeonatos mundiales de la 002 (§2.2 de la 002), incluidos los datos personales de los jugadores que solo figuran en él. |
| **Próxima temporada** | La temporada siguiente a la actual, desde que una fuente publica su calendario hasta que pasa a ser la actual (RF-3 de la 002). |
| **Ciclo** | Tiempo máximo entre dos consultas de un mismo dato: 60 segundos para los datos en vivo y 1 hora para el resto de datos, salvo las excepciones de §2.2. |
| **Ciclo de la página** | Tiempo máximo entre dos actualizaciones automáticas de una página abierta y visible: 30 segundos para los datos en vivo y 5 minutos para el resto. |
| **Umbral de desactualización** | Tiempo sin poder actualizar un dato a partir del cual se avisa al usuario: 60 segundos para los datos en vivo y 1 hora para el resto de datos. |
| **Datos de Retake** | Los que la 002 reserva a Retake y no vienen de ninguna fuente: el rol de cada jugador, las uniones y separaciones manuales de registros y la retirada de datos personales (RF-26, RF-131, RF-133 y RF-78 de la 002). |
| **Registro retenido** | Registro de una fuente que Retake guarda pero no muestra porque no ha podido enlazarlo con uno existente (RF-55). |
| **Administrador** | Hugo, única persona con acceso a la página de administración. |
| **Origen** | El dispositivo o la red desde los que alguien intenta entrar en la página de administración. |
| **Incidencia** | Cualquiera de estos casos: una consulta fallida, un dato rechazado, una consulta no realizada porque las normas de la fuente la prohíben, un partido desaparecido (RF-50), un registro retenido (RF-55), una cancelación publicada solo por una fuente secundaria (RF-53) o el bloqueo de un origen (RF-127). |
| **Registro de actualizaciones** | Lista de las consultas hechas y de sus incidencias, que solo ve el administrador. |

---

## 2. Requisitos Funcionales (Notación EARS)

### 2.1 Origen de los datos, carga inicial y entornos

* **RF-1 (Ubicuo)**: EL SISTEMA obtendrá de BreakingPoint.gg y de la web oficial de la CDL, sin intervención manual, todos los datos de la liga definidos en la spec 002, salvo los datos de Retake y los datos de la Wiki, que llegarán solo por la importación de RF-4.
  * *Nota (2026-09-23, cambio C-15, sustituye a "obtendrá de las tres fuentes, sin intervención manual"):* la Wiki bloquea el acceso automático de Retake (403 de Cloudflare) y sus condiciones exigen permiso por escrito. Hugo decide que sus datos entren por archivos CSV que él prepara y actualiza (glosario, "Archivos de la Wiki").
* **RF-2 (Ubicuo)**: EL SISTEMA aplicará a cada dato obtenido de una fuente las reglas de la spec 002 (prioridad de fuentes, validación, correcciones y datos de Retake).
* **RF-3 (Dirigido por evento)**: CUANDO Retake se ponga en marcha sin datos de la liga, EL SISTEMA obtendrá todos los datos de la temporada actual, incluidos los partidos ya finalizados.
* **RF-4 (Dirigido por evento)**: CUANDO el administrador ejecute en la terminal la importación de los archivos de la Wiki, EL SISTEMA registrará el historial completo que contienen y los datos personales de sus jugadores.
  * *Nota (2026-09-23, cambio C-16, sustituye a "CUANDO Retake se ponga en marcha sin datos de la liga, EL SISTEMA obtendrá el historial completo").*
* **RF-4a (Ubicuo)**: EL SISTEMA solo registrará los datos personales de los jugadores que figuran en el historial o en los rosters de los archivos de la Wiki.
* **RF-4b (Dirigido por evento)**: CUANDO termine la importación de RF-4, EL SISTEMA mostrará en la terminal su resultado (éxito, parcial o fallo) y sus incidencias, y lo anotará en el registro.
* **RF-4c (No deseado)**: SI falta un archivo de la Wiki o no tiene las columnas esperadas, ENTONCES EL SISTEMA no registrará nada de la importación e indicará qué archivo falla.
* **RF-5**: sin efecto (cambio C-16, 2026-09-23): el historial ya no forma parte de la carga automática.
* **RF-6 (No deseado)**: SI Retake se pone en marcha sin datos mientras no se juega ninguna temporada, ENTONCES EL SISTEMA cargará como temporada actual la última que tuvo partidos oficiales (RF-2 de la 002).
* **RF-7 (Estado)**: MIENTRAS dure la carga inicial, EL SISTEMA mostrará los datos ya cargados.
* **RF-8 (Estado)**: MIENTRAS dure la carga inicial, EL SISTEMA tratará los datos aún no cargados como datos inexistentes, no como un fallo de carga.
* **RF-9 (Opcional)**: DONDE Retake se ejecute en producción, EL SISTEMA solo mantendrá datos obtenidos de las fuentes reales.
* **RF-10 (Opcional)**: DONDE Retake se ejecute en las pruebas automáticas, EL SISTEMA usará solo los datos de prueba de la spec 002, sin consultar las fuentes reales.
* **RF-11 (Opcional)**: DONDE Retake se ejecute en el entorno de desarrollo, EL SISTEMA permitirá elegir entre los datos de prueba de la spec 002 y las fuentes reales.
* **RF-12 (Dirigido por evento)**: CUANDO se cambie de modo en el entorno de desarrollo, EL SISTEMA borrará los datos de la liga guardados en ese entorno, y el registro de actualizaciones, las incidencias y los resúmenes diarios del modo anterior.
  * *Nota (cambio C-27):* el registro de un modo no describe las fuentes del otro. En modo simulado, además, sus fechas son las del escenario (plan I-32) y aparecerían como futuras. La cuenta de administración, sus sesiones y el bloqueo por intentos fallidos se conservan.
* **RF-13 (Dirigido por evento)**: CUANDO se cambie de modo en el entorno de desarrollo, EL SISTEMA hará una carga inicial nueva con el modo elegido.
* **RF-14 (Dirigido por evento)**: CUANDO una fuente publique el calendario de la próxima temporada, EL SISTEMA lo obtendrá.
* **RF-15 (Estado)**: MIENTRAS la próxima temporada no sea la actual, EL SISTEMA no mostrará ninguno de sus datos.

### 2.2 Ciclos de consulta

* **RF-16 (Estado)**: MIENTRAS un partido esté `en vivo`, EL SISTEMA consultará sus datos en vivo al menos cada 60 segundos.
* **RF-17 (Estado)**: MIENTRAS un partido `programado` esté a 1 hora o menos de su hora de inicio programada, o la haya pasado sin pasar a `en vivo`, EL SISTEMA consultará su estado al menos cada 60 segundos.
* **RF-18 (Ubicuo)**: EL SISTEMA consultará el resto de datos al menos cada hora, salvo los partidos finalizados, que siguen RF-19 a RF-21, y los datos de la Wiki (RF-32).
* **RF-18a (No deseado)**: SI una fuente publica un partido, una posición en la tabla o un roster de la temporada actual con un equipo que no figura en su lista de equipos de esa temporada, ENTONCES EL SISTEMA consultará los datos de ese equipo y, si la fuente lo incluye en la tabla de posiciones de esa temporada, lo registrará como franquicia y lo consultará en adelante como a las demás (RF-18).
  * *Nota (cambio C-22):* le pasa a Boston Breach en 2026, que BreakingPoint ya lista como M80 Boston y con otro número. Que dos registros sean la misma franquicia lo decide la curación (RF-54 de esta spec; RF-114 de la 002). Un equipo que la fuente no incluye en la tabla se registra como equipo invitado (RF-117a de la 002; cambio C-24).
* **RF-18b (Ubicuo)**: EL SISTEMA consultará los datos de cada equipo invitado y de sus jugadores la primera vez que aparezca en un partido y, después, al menos una vez al mes.
  * *Nota (cambio C-24):* sus partidos siguen los ciclos de los demás (en vivo cada 60 s, el resto cada hora); lo mensual son su identidad, su roster y los datos de sus jugadores.
* **RF-18c (No deseado)**: SI el historial de un jugador incluye un roster de la temporada con un equipo que no es franquicia de la CDL ni equipo invitado, ENTONCES EL SISTEMA lo descartará sin registrarlo ni anotarlo en el registro.
  * *Nota (cambio C-26):* son etapas del jugador en equipos que no juegan ningún evento de la CDL (por ejemplo, en Challengers). Si ese equipo llega a jugar un evento de la CDL, pasa a ser invitado y sus rosters se registran desde entonces (RF-18b).
  * *Nota (2026-09-23, cambio C-17):* se añade la excepción de los datos de la Wiki.
* **RF-19 (Dirigido por evento)**: CUANDO un partido pase a `finalizado`, o se registre ya `finalizado`, EL SISTEMA consultará su página una vez para obtener sus estadísticas.
* **RF-20 (Dirigido por evento)**: CUANDO pasen 24, 48 y 72 horas desde la consulta de RF-19, EL SISTEMA volverá a consultar el partido, salvo si ya habían pasado más de 3 días desde su inicio cuando se registró como `finalizado`.
  * *Nota (cambio C-25):* estas tres consultas diarias valen tanto para completar estadísticas pendientes (RF-47 de la 002) como para recoger correcciones. Un partido cargado mucho después de jugarse (por ejemplo, en la primera carga de una temporada) solo se consulta una vez. El administrador puede pedir una actualización cuando quiera (RF-100).
* **RF-21 (Ubicuo)**: EL SISTEMA no consultará un partido `finalizado` fuera de los plazos de RF-19 y RF-20, salvo cuando el administrador lo pida (RF-100).
* **RF-22 (Dirigido por evento)**: CUANDO una consulta devuelva un dato nuevo o cambiado, EL SISTEMA lo registrará al terminar esa consulta.
  * *Nota:* se registra lo que devuelve cada consulta. Los valores intermedios que una fuente publique y retire entre dos consultas no se registran.
* **RF-23 (No deseado)**: SI la pausa mínima entre consultas (RF-39) impide consultar cada 60 segundos todos los partidos en vivo, ENTONCES EL SISTEMA consultará al menos cada 60 segundos el partido prioritario.
* **RF-24 (No deseado)**: SI se da el caso de RF-23, ENTONCES EL SISTEMA consultará los demás partidos en vivo al menos cada 2 minutos.
* **RF-25 (Ubicuo)**: EL SISTEMA considerará prioritario el partido que destaque la spec del spotlight.
* **RF-26 (Estado)**: MIENTRAS no esté implementada la spec del spotlight, EL SISTEMA considerará prioritario el partido en vivo con la hora de inicio programada más temprana.
* **RF-27 (No deseado)**: SI la obtención automática estuvo detenida, ENTONCES EL SISTEMA tendrá al día los datos en vivo como máximo 60 segundos después de reanudarse.
* **RF-28 (No deseado)**: SI la obtención automática estuvo detenida, ENTONCES EL SISTEMA tendrá al día el resto de datos como máximo 1 hora después de reanudarse.
* **RF-29 (No deseado)**: SI la obtención automática estuvo detenida, ENTONCES EL SISTEMA registrará solo el estado actual de lo que cambió durante la parada, sin los valores intermedios.

### 2.3 Historial de campeonatos

* **RF-30**, **RF-31** y **RF-33**: eliminados (cambio C-17, 2026-09-23). Eran las relecturas automáticas del historial tras el Champs y sus reintentos.
* **RF-32 (Ubicuo)**: EL SISTEMA solo registrará datos de la Wiki cuando el administrador ejecute la importación de RF-4.
  * *Nota (2026-09-23, cambio C-17, sustituye a la consulta del historial en la carga inicial, en las relecturas y a petición del administrador):* la importación se hace tras cada Champs, cuando el administrador actualiza los archivos; si la Wiki aún no ha publicado la clasificación completa, se vuelve a importar más tarde. Las correcciones del historial de años anteriores (RF-96 de la 002) llegan con cada importación.
* **RF-34**: sin efecto (cambio C-16, 2026-09-23): los datos personales de los jugadores del historial llegan con la importación de RF-4 y RF-4a.

### 2.4 Buen uso de las fuentes

* **RF-35 (Ubicuo)**: EL SISTEMA cumplirá las normas para programas automáticos que publique cada fuente.
* **RF-36 (Ubicuo)**: EL SISTEMA obtendrá los datos de cada fuente a través de su API pública cuando exista y, si no existe, leyendo sus páginas públicas.
  * *Nota (2026-09-23, revisión R-1, sustituye a "cumplirá las condiciones de uso de cada fuente"):* al revisar las condiciones de uso (regla P-2), las tres fuentes resultaron exigir permiso por escrito para el acceso automático (§5.2). Por la regla P-1, Hugo decidió acceder sin ese permiso, como en su proyecto `CDL-data-analysis`: API donde exista y lectura de páginas públicas donde no. A cambio, Retake limita su carga (RF-37 a RF-42) y cita las fuentes (RF-160).
* **RF-37 (Ubicuo)**: EL SISTEMA se identificará como Retake en cada consulta.
* **RF-38 (Ubicuo)**: EL SISTEMA no consultará la Wiki.
  * *Nota (2026-09-23, cambio C-18, sustituye a "consultará la Wiki solo a través del canal de acceso para programas… nunca a través de sus páginas web"):* sus datos llegan por la importación de RF-4. RF-35 a RF-42 se aplican a BreakingPoint.gg y a la web oficial de la CDL.
* **RF-39 (Ubicuo)**: EL SISTEMA dejará pasar entre dos consultas seguidas a la misma fuente al menos una pausa mínima, cuyo valor fija el plan tras revisar las condiciones de uso de esa fuente.
* **RF-40 (Ubicuo)**: EL SISTEMA respetará los límites de frecuencia de consulta que publique cada fuente.
* **RF-41 (Ubicuo)**: EL SISTEMA aplicará RF-39 y RF-40 también a las actualizaciones pedidas por el administrador.
* **RF-42 (No deseado)**: SI las normas de una fuente prohíben una consulta, ENTONCES EL SISTEMA no hará esa consulta.

### 2.5 Fallos, formatos y desapariciones

* **RF-43 (No deseado)**: SI una consulta a una fuente falla, ENTONCES EL SISTEMA conservará todos los datos ya registrados.
* **RF-44 (No deseado)**: SI una consulta a una fuente falla, ENTONCES EL SISTEMA seguirá consultando las demás fuentes con normalidad.
* **RF-45 (No deseado)**: SI una consulta a una fuente falla, ENTONCES EL SISTEMA la repetirá en el siguiente ciclo de esos datos.
* **RF-46 (No deseado)**: SI una fuente responde sin ningún dato donde antes publicaba datos, ENTONCES EL SISTEMA tratará la consulta como fallida.
* **RF-47 (No deseado)**: SI EL SISTEMA solo entiende una parte de lo que responde una fuente, ENTONCES registrará la parte que entiende.
* **RF-48 (No deseado)**: SI EL SISTEMA no entiende un dato publicado por una fuente, ENTONCES lo tratará como no publicado por esa fuente, y se aplicará la prioridad de RF-67 de la 002 entre las demás.
* **RF-49 (No deseado)**: SI ninguna fuente publica de forma legible un dato ya registrado, ENTONCES EL SISTEMA conservará el valor registrado.
* **RF-50 (No deseado)**: SI un partido registrado no aparece durante 24 horas en ninguna consulta con éxito de las fuentes que lo publicaban, y ninguna publica su cancelación, ENTONCES EL SISTEMA lo considerará desaparecido.
* **RF-51 (Ubicuo)**: EL SISTEMA conservará tal como estaba cada partido desaparecido, también si estaba `en vivo`.
  * *Nota:* un partido desaparecido solo se resuelve (por ejemplo, dándolo por cancelado) con la curación manual de la 002, fuera de la web.
* **RF-52 (No deseado)**: SI un partido desaparecido vuelve a publicarse en una fuente, ENTONCES EL SISTEMA lo actualizará como el mismo partido.
* **RF-53 (No deseado)**: SI solo publica la cancelación de un partido una fuente que no es la de mayor prioridad entre las que lo publican, ENTONCES EL SISTEMA no lo cancelará.

### 2.6 Enlace entre fuentes, marcador en vivo y datos de Retake

* **RF-54 (Ubicuo)**: EL SISTEMA considerará el mismo partido, evento, franquicia o jugador a dos registros de fuentes distintas solo si una fuente los relaciona o Retake los une a mano.
* **RF-55 (No deseado)**: SI un registro de una fuente no está enlazado con ninguno existente y una fuente de mayor prioridad publica registros de ese mismo tipo, ENTONCES EL SISTEMA lo retendrá sin mostrarlo.
  * *Nota (2026-09-23, cambio C-14, aprobado por Hugo durante la fase F4):* retener significa no mostrarlo en los datos de la temporada actual (listas de jugadores, equipos y partidos). El historial de campeonatos sí lo usa: la fuente de mayor prioridad (BreakingPoint) no publica historial, así que no puede duplicarlo. Sin esta nota, todo el historial de la Wiki quedaría oculto hasta confirmarlo registro a registro.
* **RF-56 (Dirigido por evento)**: CUANDO Retake una a mano un registro retenido con uno existente, o lo confirme como nuevo, EL SISTEMA dejará de retenerlo.
* **RF-57 (Estado)**: MIENTRAS un partido esté `en vivo`, EL SISTEMA tomará como marcador el más avanzado que publique cualquier fuente, sin aplicar la prioridad de RF-67 de la 002.
* **RF-58 (Ubicuo)**: EL SISTEMA considerará más avanzado el marcador con más mapas terminados y, si empatan, el que sume más puntos, rondas u overloads entre los dos equipos en el mapa en curso.
* **RF-59 (Estado)**: MIENTRAS un partido esté `en vivo`, EL SISTEMA no registrará un marcador menos avanzado que el ya registrado.
  * *Nota:* la excepción de RF-57 a RF-59 solo vale mientras el partido está `en vivo`. El marcador final de un partido `finalizado` sigue la prioridad de RF-67 de la 002.
* **RF-60 (No deseado)**: SI se han retirado los datos personales de un jugador (RF-78 de la 002), ENTONCES EL SISTEMA no volverá a registrarlos aunque las fuentes los publiquen, mientras Retake no revierta la retirada a mano.

### 2.7 Identidades y logos

* **RF-61 (No deseado)**: SI dos fuentes publican identidades distintas de la misma franquicia vigentes en la misma fecha, ENTONCES EL SISTEMA mantendrá una sola identidad vigente.
* **RF-62 (Ubicuo)**: EL SISTEMA tomará cada campo de una identidad (nombre corto, abreviatura, logo, color primario, color secundario y fecha y hora de vigencia) de la fuente con más prioridad que lo publique (RF-67 de la 002).
* **RF-63 (Ubicuo)**: EL SISTEMA solo registrará una identidad nueva (RF-73 de la 002) cuando cambie el resultado de combinar los campos según RF-62.
* **RF-64 (No deseado)**: SI después de combinar los campos una identidad sigue sin logo, ENTONCES EL SISTEMA aplicará las reglas de logo ausente de la 002 (RF-14, RF-15 y RF-118 de la 002).
* **RF-65 (Dirigido por evento)**: CUANDO EL SISTEMA reciba un logo de una fuente, guardará una copia propia.
* **RF-66 (No deseado)**: SI EL SISTEMA recibe una imagen idéntica a un logo del que ya tiene copia, ENTONCES no guardará otra copia.
* **RF-67 (No deseado)**: SI cambia la imagen de un logo aunque su dirección sea la misma, ENTONCES EL SISTEMA la tratará como un logo nuevo.
* **RF-68 (Ubicuo)**: EL SISTEMA solo guardará como copia de logo imágenes en formatos que no pueden contener código ejecutable.
* **RF-69 (Ubicuo)**: EL SISTEMA solo guardará como copia de logo imágenes de 1 MB como máximo.
* **RF-70 (No deseado)**: SI un logo incumple RF-68 o RF-69, o no se puede obtener su imagen, ENTONCES EL SISTEMA lo tratará como logo no registrado.
* **RF-71 (No deseado)**: SI una fuente deja de publicar un logo del que Retake tiene copia, ENTONCES EL SISTEMA seguirá usando la copia.

### 2.8 Temporada actual y año del pie

* **RF-72 (Ubicuo)**: EL SISTEMA aplicará el cambio de temporada (RF-2, RF-3 y RF-123 de la 002) solo a partir de los datos obtenidos de las fuentes, sin ningún valor mantenido a mano.
* **RF-73 (Ubicuo)**: EL SISTEMA considerará que un partido pertenece a la temporada de su evento aunque se juegue después de que empiece la siguiente (RF-53 de la 002).
* **RF-74 (Ubicuo)**: EL SISTEMA mostrará en el pie de página el año de la temporada actual calculada según RF-72.
* **RF-75 (Dirigido por evento)**: CUANDO cambie la temporada actual, EL SISTEMA mostrará el nuevo año en el pie de las páginas abiertas y visibles como máximo 5 minutos después.
* **RF-76 (No deseado)**: SI una página no ha obtenido todavía la temporada actual, ENTONCES EL SISTEMA mostrará el pie sin el año.
* **RF-77 (Dirigido por evento)**: CUANDO se obtenga la temporada actual después de haber mostrado el pie sin el año, EL SISTEMA añadirá el año al pie.
* **RF-78 (No deseado)**: SI falla la actualización de la temporada cuando el pie ya muestra el año, ENTONCES EL SISTEMA mantendrá el año mostrado.

### 2.9 Actualización de las páginas abiertas

* **RF-79 (Estado)**: MIENTRAS una página con datos de la liga esté abierta y visible, EL SISTEMA mostrará en ella los datos nuevos sin que el usuario la recargue.
* **RF-80 (Dirigido por evento)**: CUANDO EL SISTEMA registre un dato en vivo, lo mostrará en las páginas abiertas y visibles que lo contengan como máximo 30 segundos después.
* **RF-81 (Dirigido por evento)**: CUANDO EL SISTEMA registre un dato del resto de datos, lo mostrará en las páginas abiertas y visibles que lo contengan como máximo 5 minutos después.
* **RF-82 (Dirigido por evento)**: CUANDO una página abierta vuelva a ser visible, EL SISTEMA mostrará en ella los datos al día como máximo 5 segundos después.
* **RF-83 (Ubicuo)**: EL SISTEMA conservará, al mostrar datos nuevos, la posición de scroll, el elemento con el foco del teclado, las pestañas internas abiertas, la diapositiva visible de cada carrusel y los filtros u orden elegidos por el usuario.
* **RF-84 (No deseado)**: SI un elemento cambia de posición al mostrar datos nuevos, ENTONCES EL SISTEMA no desplazará la vista del usuario.
* **RF-85 (Ubicuo)**: EL SISTEMA no mostrará el esqueleto de carga de la 001 (RF-40 de la 001) mientras actualiza un bloque que ya muestra datos.
* **RF-86 (No deseado)**: SI falla la actualización automática de un bloque que ya muestra datos, ENTONCES EL SISTEMA seguirá mostrando esos datos.
* **RF-87 (No deseado)**: SI falla la actualización automática de un bloque que ya muestra datos, ENTONCES EL SISTEMA no mostrará en él el aviso de error ni el botón "Reintentar" de la 001 (RF-41 de la 001).
* **RF-88 (No deseado)**: SI falla la actualización automática de un bloque que ya muestra datos, ENTONCES EL SISTEMA lo volverá a intentar en el siguiente ciclo de la página.
* **RF-89 (No deseado)**: SI los datos de un bloque llevan más tiempo que su umbral de desactualización sin poder actualizarse, porque falla la conexión entre la página y Retake o la fuente de alguno de esos datos, ENTONCES EL SISTEMA mostrará en el bloque un aviso discreto de datos sin actualizar.
  * *Nota (2026-09-23, cambio C-20):* no se aplica a los bloques que solo muestran datos de la Wiki, como el historial: esos datos solo cambian al importar (RF-32).
* **RF-90 (No deseado)**: SI un partido `en vivo` lleva más de 60 segundos sin aparecer en ninguna consulta con éxito de las fuentes que lo publicaban, ENTONCES EL SISTEMA mostrará el aviso de RF-89 en los bloques que lo muestran.
* **RF-91 (Ubicuo)**: EL SISTEMA mostrará el aviso de RF-89 sin retirar el contenido del bloque.
* **RF-92 (Dirigido por evento)**: CUANDO un bloque con el aviso de RF-89 vuelva a actualizarse con éxito, EL SISTEMA retirará el aviso.
* **RF-93 (Ubicuo)**: EL SISTEMA no indicará al usuario final qué ha fallado, si la conexión o la fuente, ni que un partido ha desaparecido de las fuentes.
* **RF-94 (Ubicuo)**: EL SISTEMA cumplirá el nivel AA de las WCAG 2.2 en todo bloque que se actualice de forma automática.
* **RF-95 (Dirigido por evento)**: CUANDO cambie un dato en vivo visible en la página, EL SISTEMA anunciará el cambio a los lectores de pantalla sin interrumpir lo que estén leyendo.
* **RF-96 (Ubicuo)**: EL SISTEMA no anunciará a los lectores de pantalla los cambios del resto de datos.

### 2.10 Página de administración

* **RF-97 (Ubicuo)**: EL SISTEMA ofrecerá una página de administración, también en producción.
* **RF-98 (Ubicuo)**: EL SISTEMA mostrará la página de administración y su pantalla de acceso dentro del marco común de la 001, sin ninguna entrada del menú activa.
* **RF-99 (Ubicuo)**: EL SISTEMA no mostrará en el menú ninguna entrada que lleve a la página de administración.
* **RF-100 (Dirigido por evento)**: CUANDO el administrador pida actualizar una fuente, EL SISTEMA iniciará, sin esperar al siguiente ciclo, una consulta de todos los datos de la temporada actual que publica esa fuente.
  * *Nota (2026-09-23, cambio C-19):* la Wiki no está entre las fuentes que se pueden actualizar; sus datos llegan por la importación de RF-4.
* **RF-101 (Ubicuo)**: EL SISTEMA no incluirá el historial en la actualización de una fuente pedida por el administrador.
* **RF-102**: eliminado (cambio C-19, 2026-09-23). Releer el historial desde la página de administración; lo sustituye la importación de RF-4.
* **RF-103 (Estado)**: MIENTRAS una actualización pedida por el administrador esté en curso, EL SISTEMA lo indicará en la página de administración.
* **RF-104 (Dirigido por evento)**: CUANDO termine una actualización pedida por el administrador, EL SISTEMA mostrará su resultado: éxito, parcial o fallo.
* **RF-105 (Ubicuo)**: EL SISTEMA considerará una actualización como éxito si no tuvo incidencias, como parcial si tuvo alguna consulta con éxito y alguna incidencia, y como fallo si ninguna consulta tuvo éxito.
* **RF-106 (Dirigido por evento)**: CUANDO termine una actualización pedida por el administrador, EL SISTEMA mostrará su número de incidencias con acceso al detalle de cada una en el registro.
* **RF-107 (No deseado)**: SI el administrador pide actualizar una fuente que ya se está actualizando, ENTONCES EL SISTEMA mantendrá una única actualización en curso para esa fuente.
* **RF-108**: eliminado (cambio C-19, 2026-09-23).
* **RF-109 (No deseado)**: SI se da el caso de RF-107, ENTONCES EL SISTEMA indicará en la página de administración que ya hay una en curso.
  * *Nota (2026-09-23, cambio C-19):* se quita el caso de RF-108, eliminado.
* **RF-110 (No deseado)**: SI el administrador pide una actualización que las normas de la fuente prohíben en ese momento (RF-40, RF-42), ENTONCES EL SISTEMA no la hará.
* **RF-111 (No deseado)**: SI se da el caso de RF-110, ENTONCES EL SISTEMA indicará el motivo en la página de administración.
* **RF-112 (Ubicuo)**: EL SISTEMA mostrará en la página de administración la hora de la última consulta a cada fuente.
* **RF-113 (Ubicuo)**: EL SISTEMA mostrará en la página de administración la hora de la última consulta con éxito a cada fuente.
  * *Nota (2026-09-23, cambio C-19):* para la Wiki, la hora de la última importación con éxito de sus archivos.
* **RF-114 (No deseado)**: SI pasa más del doble del ciclo más corto que tenga una fuente en ese momento sin ninguna consulta a ella, ENTONCES EL SISTEMA la marcará como parada en la página de administración.
  * *Nota (2026-09-23, cambio C-19):* no se aplica a la Wiki, que no tiene ciclo.
* **RF-115 (Ubicuo)**: EL SISTEMA aplicará a cada parte de la página de administración las reglas de carga, error y conexión de los bloques de la 001 (RF-40 a RF-53 de la 001).
* **RF-116 (Estado)**: MIENTRAS el dispositivo no tenga conexión, EL SISTEMA desactivará en la página de administración las peticiones de actualización.
* **RF-117 (Ubicuo)**: EL SISTEMA aplicará a la página de administración y a su pantalla de acceso las reglas de idioma de la spec 001 (§2.10 de la 001).
* **RF-118 (Ubicuo)**: EL SISTEMA mostrará sin traducir los mensajes de error recibidos de las fuentes.
* **RF-119 (Ubicuo)**: EL SISTEMA mostrará como texto plano todo texto recibido de una fuente, incluidos sus mensajes de error.
* **RF-120 (Ubicuo)**: EL SISTEMA recortará a 500 caracteres cada mensaje de error de una fuente, terminándolo en "…".

### 2.11 Acceso del administrador

* **RF-121 (Ubicuo)**: EL SISTEMA tendrá una única cuenta con acceso a la página de administración, la del administrador.
* **RF-122 (Ubicuo)**: EL SISTEMA no ofrecerá en la web ninguna forma de crear cuentas.
* **RF-123 (Ubicuo)**: EL SISTEMA no ofrecerá en la web ninguna forma de cambiar o recuperar la contraseña del administrador.
* **RF-124 (Dirigido por evento)**: CUANDO alguien abra la página de administración sin una sesión activa, EL SISTEMA le pedirá usuario y contraseña.
* **RF-125 (Dirigido por evento)**: CUANDO el administrador introduzca su usuario y su contraseña correctos, EL SISTEMA abrirá una sesión.
* **RF-126 (No deseado)**: SI se introducen un usuario o una contraseña incorrectos, ENTONCES EL SISTEMA denegará el acceso sin indicar cuál de los dos es incorrecto.
* **RF-127 (No deseado)**: SI desde un mismo origen se introducen credenciales incorrectas 5 veces seguidas, ENTONCES EL SISTEMA bloqueará ese origen durante 15 minutos.
* **RF-128 (Ubicuo)**: EL SISTEMA contará para RF-127 los intentos con cualquier usuario, incluidos los que no existen.
* **RF-129 (Estado)**: MIENTRAS un origen esté bloqueado, EL SISTEMA denegará desde él también las credenciales correctas.
* **RF-130 (Estado)**: MIENTRAS un origen esté bloqueado, EL SISTEMA permitirá el acceso desde los demás orígenes.
* **RF-131 (Dirigido por evento)**: CUANDO haya un acceso correcto desde un origen, EL SISTEMA pondrá a cero su contador de intentos fallidos.
* **RF-132 (Dirigido por evento)**: CUANDO termine el bloqueo de un origen, EL SISTEMA pondrá a cero su contador de intentos fallidos.
* **RF-133 (Dirigido por evento)**: CUANDO EL SISTEMA bloquee un origen, lo anotará como incidencia en el registro.
* **RF-134 (Ubicuo)**: EL SISTEMA cerrará cada sesión 8 horas después de abrirla.
* **RF-135 (Ubicuo)**: EL SISTEMA permitirá tener varias sesiones del administrador abiertas a la vez.
* **RF-136 (No deseado)**: SI una sesión caduca con una actualización pedida en curso, ENTONCES EL SISTEMA terminará igualmente esa actualización.
* **RF-137 (Dirigido por evento)**: CUANDO el administrador intente una acción con la sesión caducada, EL SISTEMA le pedirá de nuevo usuario y contraseña.
* **RF-138 (Dirigido por evento)**: CUANDO el administrador pulse "Cerrar sesión", EL SISTEMA cerrará su sesión.
* **RF-139 (Ubicuo)**: EL SISTEMA solo permitirá pedir actualizaciones, consultar el registro y ver los resúmenes a una sesión abierta del administrador.

### 2.12 Registro de actualizaciones y resumen diario

* **RF-140 (Dirigido por evento)**: CUANDO termine una consulta a una fuente, EL SISTEMA añadirá al registro la fuente, la hora y el resultado de la consulta.
* **RF-141 (No deseado)**: SI una consulta falla, ENTONCES EL SISTEMA anotará en el registro el motivo del fallo.
* **RF-142 (No deseado)**: SI EL SISTEMA rechaza un dato, ENTONCES anotará en el registro el dato y el motivo del rechazo, por ejemplo un valor imposible (RF-100 de la 002), una referencia desconocida, un dato que no entiende (RF-48) o un logo no válido (RF-70).
* **RF-143 (No deseado)**: SI EL SISTEMA no hace una consulta porque las normas de la fuente la prohíben, ENTONCES lo anotará en el registro con la norma que la prohíbe.
* **RF-144 (No deseado)**: SI un partido pasa a estar desaparecido (RF-50), ENTONCES EL SISTEMA lo anotará en el registro.
* **RF-145 (No deseado)**: SI EL SISTEMA retiene un registro (RF-55), ENTONCES lo anotará en el registro.
* **RF-146 (No deseado)**: SI EL SISTEMA no cancela un partido por RF-53, ENTONCES anotará la discrepancia en el registro.
* **RF-147 (No deseado)**: SI se repite una incidencia idéntica (misma fuente, mismo dato, mismo valor y mismo motivo), ENTONCES EL SISTEMA no añadirá una entrada nueva al registro.
* **RF-148 (No deseado)**: SI se da el caso de RF-147, ENTONCES EL SISTEMA actualizará en la entrada existente el número de repeticiones y la hora de la última.
* **RF-149 (Dirigido por evento)**: CUANDO pasen 7 días desde la última repetición de una entrada del registro, EL SISTEMA la eliminará.
* **RF-150 (Dirigido por evento)**: CUANDO termine un día natural, a las 00:00 de la hora de Ciudad de México, con al menos una incidencia, EL SISTEMA mostrará en la página de administración un resumen de las incidencias de ese día.
* **RF-151 (Ubicuo)**: EL SISTEMA incluirá en cada resumen, por fuente, el número de consultas fallidas y de datos rechazados del día.
* **RF-152 (Ubicuo)**: EL SISTEMA incluirá en cada resumen, por fuente, la lista de incidencias distintas del día, con su número de repeticiones y acceso a su detalle en el registro.
* **RF-153 (No deseado)**: SI un día natural termina sin ninguna incidencia, ENTONCES EL SISTEMA no generará resumen de ese día.
* **RF-154 (Dirigido por evento)**: CUANDO un resumen cumpla 7 días, EL SISTEMA lo eliminará.

### 2.13 Reglas comunes de presentación

Igual que el §2.9 de la 002, estas reglas obligan a todas las specs visuales (004 en adelante). Cada una decide dónde y con qué diseño se aplican, pero no puede contradecirlas. Las reglas de RF-79 a RF-96 también obligan a las specs visuales.

* **RF-155 (Ubicuo)**: EL SISTEMA mostrará en cada bloque o página con datos de la liga cuándo fue su última actualización, también cuando no tenga datos que mostrar.
* **RF-156 (Ubicuo)**: EL SISTEMA no mostrará la hora de última actualización en el pie de página, en la página de administración ni en el bloque de demostración de la 001.
* **RF-157 (Ubicuo)**: EL SISTEMA considerará como última actualización de un bloque o página el momento en que Retake registró el cambio más reciente de los datos que muestra.
* **RF-158 (Opcional)**: DONDE un bloque no tenga datos que mostrar, EL SISTEMA considerará como su última actualización el último cambio registrado de los datos que vigila (ej. los partidos en vivo, en un bloque que dice que no hay ninguno).
* **RF-159 (Ubicuo)**: EL SISTEMA considerará cambio también el primer registro de un dato.
* **RF-160 (Ubicuo)**: EL SISTEMA mostrará en el pie de página de todas las páginas el nombre de cada una de las tres fuentes, con un enlace a cada una.
  * *Nota (2026-09-23, revisión R-1):* cumple la atribución que exige la licencia CC BY-SA del texto de la Wiki y cita también a BreakingPoint.gg y a la web oficial de la CDL. Requiere el cambio C-11 en la 001.

### 2.14 Reglas de proceso

Estas reglas rigen el desarrollo, no el comportamiento de la web, así que no llevan número de requisito.

* **P-1**: Si las normas o las condiciones de uso de una fuente impiden cumplir un requisito de esta spec (por ejemplo, la pausa mínima de RF-39 frente a los 60 segundos de RF-16), el requisito se marca como `[NECESITA ACLARACIÓN]` y se detiene su desarrollo hasta que Hugo decida, sin rebajarlo por cuenta propia. Se aplica al redactar el plan y en cualquier momento posterior en que cambien las normas de una fuente.
* **P-2**: El primer paso del plan es revisar las condiciones de uso de las tres fuentes (RF-36) y fijar la pausa mínima de cada una (RF-39).

---

## 3. Casos Límite y Manejo de Errores

1. **Datos vacíos o no disponibles**:
   - Primera puesta en marcha → se carga la temporada actual; el historial llega cuando el administrador importa los archivos de la Wiki. Mientras tanto, la web muestra lo ya cargado y trata lo demás como "sin datos", no como error (RF-3, RF-4, RF-6 a RF-8; cambio C-21).
   - Primera puesta en marcha entre temporadas → se carga la última temporada con partidos oficiales (RF-6).
   - Dato que ninguna fuente publica de forma legible → ausente si nunca se registró; si ya estaba registrado, se conserva (RF-48, RF-49).
   - Logo que no se puede obtener, demasiado grande o en un formato que puede contener código → logo no registrado, con las reglas de la 002 (RF-68 a RF-70).
   - Pie sin temporada → sin año hasta obtenerla; si ya tenía año, lo mantiene (RF-76 a RF-78).
   - Champs cuya clasificación la Wiki aún no ha publicado → entra con los datos disponibles y se completa con una nueva importación cuando el administrador actualiza los archivos (RF-4, RF-32; cambio C-21).
   - Archivo de la Wiki que falta o con otras columnas → no se registra nada de la importación y se indica qué archivo falla (RF-4c; cambio C-21).
   - Bloque sin datos → muestra igualmente la hora de la última actualización de lo que vigila (RF-155, RF-158).
2. **Entradas no válidas**:
   - Respuesta entendida a medias → se registra lo que se entiende; lo ilegible cuenta como no publicado por esa fuente y se anota (RF-47, RF-48, RF-142).
   - Respuesta vacía donde antes había datos → consulta fallida, no desaparición en bloque (RF-46).
   - Equipo de un partido que la fuente no incluye en su lista → se consultan sus datos: si está en la tabla de la temporada, franquicia (RF-18a; la curación lo une a su nombre siguiente, RF-54); si no, equipo invitado (RF-18b; cambios C-22 y C-24).
   - Registro de una fuente secundaria que no se puede enlazar → retenido sin mostrar hasta que Retake lo una o lo confirme como nuevo, para que el usuario nunca vea duplicados (RF-54 a RF-56).
   - Identidades distintas entre fuentes → una sola, campo a campo; solo nace una identidad nueva si cambia el resultado combinado (RF-61 a RF-64).
   - Cancelación publicada solo por una fuente secundaria → no se cancela y se anota (RF-53, RF-146).
   - Mensaje de error enorme o con código → texto plano recortado a 500 caracteres (RF-119, RF-120).
   - Credenciales incorrectas → acceso denegado sin decir qué falló; con 5 fallos seguidos, ese origen queda bloqueado 15 minutos, pero Hugo puede entrar desde otro (RF-126 a RF-133).
3. **Peticiones lentas o interrumpidas**:
   - Fuente caída → se conservan sus datos, las demás siguen y se reintenta en el siguiente ciclo (RF-43 a RF-45). Pasado el umbral, los bloques afectados muestran un aviso discreto, sin decir qué falló (RF-89, RF-93).
   - Actualización automática fallida en una página abierta → el bloque conserva sus datos, sin error ni "Reintentar"; tras el umbral, aviso discreto (RF-86 a RF-92).
   - Obtención automática detenida → al volver, los datos en vivo se ponen al día en 60 segundos y el resto en 1 hora, solo con su estado actual (RF-27 a RF-29). En la página de administración la fuente aparece como parada (RF-114); la Wiki no, porque no tiene ciclo (cambio C-21).
   - Primera carga de un bloque que falla → sigue la regla de la 001 (aviso de error y "Reintentar"), que esta spec no cambia.
   - Pestaña en segundo plano o dispositivo en reposo → no se actualiza; al volver a verse, se pone al día en 5 segundos (RF-79 a RF-82).
   - Página de administración sin conexión o con el servidor caído → reglas de bloque de la 001 y peticiones de actualización desactivadas (RF-115, RF-116).
4. **Fuentes que cambian o desaparecen**:
   - Partido que falta en las fuentes → a los 60 segundos, si estaba en vivo, aviso discreto (RF-90); a las 24 horas, desaparecido: se conserva tal cual, también si estaba en vivo, y se anota (RF-50, RF-51, RF-144). Si reaparece, se actualiza como el mismo partido (RF-52).
   - Logo retirado por la fuente → se sigue usando la copia propia (RF-71). Logo cuya imagen cambia sin cambiar de dirección → logo nuevo (RF-67).
   - Fuente que cierra o pasa a ser de pago → no hay tratamiento especial: Hugo lo ve en la última consulta con éxito y en el resumen diario (RF-113, RF-150).
   - Norma de una fuente que prohíbe una consulta → no se hace y se anota; si impide cumplir la spec, se aplica P-1 (RF-42, RF-143).
5. **Varios partidos en vivo a la vez**: si la pausa mínima no permite consultarlos todos cada 60 segundos, el prioritario (el del spotlight o, mientras no exista su spec, el que empezó antes) mantiene los 60 segundos y los demás pasan a 2 minutos (RF-23 a RF-26).
6. **Marcadores en vivo contradictorios**: vale el más avanzado de cualquier fuente y nunca retrocede; al finalizar, el marcador final vuelve a seguir la prioridad de la 002 (RF-57 a RF-59).
7. **Cambio de temporada**: el calendario de la próxima temporada se obtiene sin mostrarse. Un partido pospuesto sigue siendo de la temporada de su evento. Las páginas abiertas pasan a la nueva temporada en 5 minutos como máximo (RF-14, RF-15, RF-73, RF-75, RF-81).
8. **Retirada de datos personales**: nunca vuelven a registrarse aunque las fuentes los sigan publicando (RF-60).
9. **Hora de actualización engañosa**: con "último cambio", un partido parado muestra una hora antigua sin que nada falle. El aviso de RF-89 solo aparece cuando de verdad no se puede actualizar (RF-157, RF-89).
10. **Bloqueo de acceso**: el bloqueo es por origen, así que un atacante no puede dejar a Hugo sin acceso desde cualquier sitio. Cada bloqueo se anota (RF-127 a RF-133).

---

## 4. Fuera de Alcance

* Fuentes distintas de las tres de RF-66 de la 002.
* Estadísticas de los jugadores en el mapa en curso; solo las de los mapas ya terminados son datos en vivo.
* Diseño, texto y posición de la hora de última actualización y del aviso de datos sin actualizar; los decide cada spec visual (RF-89, RF-155).
* Indicar al usuario final qué ha fallado (la conexión o la fuente) o que un partido ha desaparecido (RF-93).
* Un control para pausar las actualizaciones automáticas de la página.
* Avisos al administrador fuera de la página de administración (correo, mensajería, notificaciones).
* Tratamiento especial de una fuente cerrada de forma permanente, y cambiar de fuente (sería una spec nueva).
* Cancelación o finalización automáticas de partidos desaparecidos.
* Resolver desde la web los partidos desaparecidos y los registros retenidos: se hace con la curación manual de la 002, fuera de la web.
* Enlazar registros de fuentes distintas por coincidencia de datos (equipos, fecha, nombre); solo cuentan los enlaces de las fuentes y las uniones manuales (RF-54).
* Conservar el registro de actualizaciones y los resúmenes más de 7 días.
* Herramientas para asignar roles, unir o separar registros, confirmar registros retenidos y retirar datos personales (datos de Retake); siguen fuera de alcance, como en la 002.
* Cuentas de usuario para el público, más cuentas de administrador y gestión de cuentas.
* Cambiar o recuperar la contraseña del administrador desde la web (RF-123); se hace fuera de la web.
* Consultar la Wiki (RF-38; cambio C-18).
* Obtener y actualizar los archivos de la Wiki: los prepara el administrador fuera de Retake (cambio C-18).
* Logos en formatos que pueden contener código (por ejemplo, SVG), y copias propias de imágenes distintas de los logos (como fotos de jugadores, que la 002 ya excluye).
* Mostrar datos de la próxima temporada antes de que sea la actual (RF-15).
* Diseño visual de la página de administración más allá de sus funciones.

---

## 5. Dudas y Aclaraciones Pendientes

### 5.1 Decisiones tomadas con Hugo (2026-09-23)

**Entrevista inicial:**

| # | Duda | Decisión | Requisitos |
|---|---|---|---|
| 1 | Fuentes que cubre la 003 | Las tres fuentes de RF-66 de la 002 | RF-1 |
| 2 | Retraso máximo del marcador en vivo | 60 segundos. *Reformulado como ciclo de consulta en Q-40* | RF-16 |
| 3 | Retraso máximo del cambio de estado de un partido | 60 segundos, igual que el marcador | RF-16, RF-17 |
| 4 | Retraso máximo del resto de datos | 1 hora | RF-18 |
| 5 | Frecuencia de revisión del historial | Carga inicial, relectura completa tras cada Champs y relectura a petición | RF-4, RF-30 a RF-32, RF-102 |
| 6 | Conflicto con RF-96 de la 002 (correcciones del historial) | Se resuelve con la relectura completa tras cada Champs y a petición | RF-30 a RF-32, RF-102, §5.3 |
| 7 | Actualización a petición del resto de fuentes | Sí, de cualquier fuente | RF-100 |
| 8 | Qué sabe el usuario final de la antigüedad de los datos | Siempre ve cuándo se actualizó el bloque | RF-155 |
| 9 | Nivel de la hora de actualización | Una por bloque o página | RF-155 |
| 10 | Significado de "actualizado" | Último cambio de un dato, no última consulta con éxito | RF-157, RF-159 |
| 11 | Aviso al usuario final de una fuente caída | No; basta con la hora. *Sustituida por Q-11 y Q-12* | RF-89, RF-93 |
| 12 | Hora mostrada en un bloque con datos de distintas edades | La del cambio más reciente | RF-157 |
| 13 | Cómo se entera Hugo de los fallos | Registro consultable más resumen diario | RF-140 a RF-154 |
| 14 | Frecuencia del aviso | Un resumen diario | RF-150 |
| 15 | Resumen en días sin incidencias | No se genera | RF-153 |
| 16 | Conservación del registro | 7 días | RF-149 |
| 17 | Normas de buen uso | Cumplir las normas para programas, las condiciones de uso y los límites; si impiden cumplir la spec, se detiene el desarrollo hasta que Hugo decida | RF-35 a RF-42, P-1 |
| 18 | Logos | Copia propia de cada logo | RF-65, RF-71 |
| 19 | Identidades distintas entre fuentes (ajuste I-15 de la 002) | Una sola identidad, campo a campo según la prioridad de fuentes | RF-61, RF-62 |
| 20 | Datos de prueba de la 002 | Solo en desarrollo y en las pruebas; en producción, solo fuentes reales | RF-9 a RF-11 |
| 21 | Año del pie | Entra en la 003: automático, sin valor manual | RF-72, RF-74, RF-75 |
| 22 | Pie sin temporada disponible | Se omite el año y se añade al obtenerlo | RF-76, RF-77 |
| 23 | Páginas abiertas | Regla común: se actualizan sin recargar | RF-79 |
| 24 | Margen hasta mostrarlo en pantalla | 30 s para los datos en vivo y 5 min para el resto | RF-80, RF-81 |
| 25 | Actualización automática fallida en un bloque con datos | Se conservan los datos sin error. *Matizada por Q-11: aviso discreto tras el umbral* | RF-86 a RF-88 |
| 26 | Respuesta entendida solo en parte | Se registra lo que se entiende | RF-47, RF-48 |
| 27 | Dato ya registrado que deja de entenderse | Se conserva el valor registrado. *Matizada por Q-3: antes se busca en las demás fuentes* | RF-49 |
| 28 | Partido que desaparece sin cancelación | Se conserva y se anota en el registro | RF-50, RF-51, RF-144 |
| 29 | Dónde actúa el administrador | Página privada en la web | RF-97 a RF-120 |
| 30 | Acceso a la página privada | Una única cuenta, sin registro en la web | RF-121 a RF-126 |
| 31 | Caducidad de la sesión y bloqueo | Sesión de 8 horas; 5 intentos fallidos seguidos bloquean 15 minutos. *El bloqueo pasa a ser por origen en Q-33* | RF-127, RF-134 |
| 32 | Canal del resumen diario | Aviso en la página de administración | RF-150 |

**Segunda ronda (pendientes del borrador):**

| # | Duda | Decisión | Requisitos |
|---|---|---|---|
| 33 | La Wiki rechazaba las peticiones automáticas | Basarse en los scripts de extracción de `CDL-data-analysis`: consultar la Wiki solo a través de su canal para programas, identificándose y con pausa entre peticiones | RF-37 a RF-39 |
| 34 | El script de BreakingPoint se hace pasar por un navegador | Retake se identifica como Retake también en BreakingPoint, sin excepciones | RF-37 |
| 35 | Cuándo se revisan las condiciones de uso | Como primer paso del plan; si alguna prohíbe algo que la spec necesita, se aplica P-1 | RF-36, P-1, P-2 |
| 36 | Plazo de la relectura tras un Champs | Primera relectura como máximo 1 h después de la final; luego una cada 24 h durante 7 días | RF-30, RF-31 |
| 37 | Peticiones repetidas de actualizar una fuente | Una sola actualización en curso por fuente | RF-107 |
| 38 | Cierre del periodo del resumen diario | Día natural, a las 00:00 de la hora de Ciudad de México | RF-150, RF-153 |
| 39 | Conservación de los resúmenes | 7 días, igual que el registro | RF-154 |
| 40 | Cambio o recuperación de la contraseña | Solo fuera de la web | RF-123 |
| 41 | Idioma de la página de administración | Español e inglés, con las reglas de la 001; los mensajes de error de las fuentes, sin traducir | RF-117, RF-118 |

**Resolución de la revisión QA** (entre corchetes, el número del hallazgo):

| # | Hallazgo | Decisión | Requisitos |
|---|---|---|---|
| Q-1 | [2.1] Sin conocer la próxima temporada, la actual no cambiaría nunca | Se obtiene el calendario de la próxima temporada sin mostrarlo hasta que sea la actual | RF-14, RF-15 |
| Q-2 | [2.2, 2.3] Combinar campos frente a RF-14 y RF-73 de la 002 | Primero se combinan las fuentes; solo hay identidad nueva si cambia el resultado combinado; después se aplican las reglas de logo ausente | RF-62 a RF-64 |
| Q-3 | [2.4] Dato ilegible en la fuente principal y publicado por otra | Lo ilegible cuenta como no publicado y manda la siguiente fuente | RF-48, RF-49 |
| Q-4 | [2.5] Marcador en vivo más nuevo en una fuente secundaria | Vale el más avanzado de cualquier fuente y nunca retrocede (excepción a RF-67 de la 002, solo en vivo) | RF-57 a RF-59 |
| Q-5 | [2.6] Relecturas del historial fallidas o perdidas | Se reintentan cada hora hasta completarse | RF-32, RF-33 |
| Q-6 | [2.7] Datos de prueba y entorno de pruebas | Desarrollo y pruebas sí; producción nunca; las pruebas no consultan fuentes reales | RF-9 a RF-11 |
| Q-7 | [2.8] Página de administración frente a la 001 | Usa el marco común sin entrada activa; se anota en la 001 que el acceso del administrador lo define la 003 | RF-98, §5.3 |
| Q-8 | [2.9] Mensajes sin traducir frente a RF-63 de la 001 | Excepción anotada: son datos, no textos de la interfaz; el texto que los rodea sí se traduce | RF-117, RF-118, §5.3 |
| Q-9 | [2.10] Pausa entre peticiones sin requisito | Pausa mínima entre consultas a cualquier fuente; su valor lo fija el plan | RF-39, RF-41, P-2 |
| Q-10 | [2.11] Cancelación contradictoria entre fuentes | Manda la prioridad de fuentes; la discrepancia se anota | RF-53, RF-146 |
| Q-11 | [4.1] Constitución §4.3 (indicadores de fallo) | Aviso discreto de datos sin actualizar al superar el umbral, sin retirar el contenido | RF-89, RF-91, RF-92 |
| Q-12 | [4.1] Qué fallos activan el aviso | Tanto la conexión página–Retake como la fuente; no se dice cuál | RF-89, RF-93 |
| Q-13 | [4.2] Accesibilidad del contenido que se actualiza solo | WCAG 2.2 AA; se anuncian solo los cambios en vivo, sin interrumpir | RF-94 a RF-96 |
| Q-14 | [4.3] Requisitos añadidos sin decisión de Hugo | Confirmados todos: recuperación tras parada, estado de la página, sin esqueleto al actualizar, credenciales sin detalle, "Cerrar sesión", el primer registro cuenta como cambio y el riesgo de bloqueo | RF-27 a RF-29, RF-83, RF-85, RF-126, RF-138, RF-159 |
| Q-15 | [4.4] Detalles técnicos en la spec | Requisitos en lenguaje neutro; lo técnico pasa a notas para el plan | RF-35, RF-38, §5.2 |
| Q-16 | [4.5] Mensajes de error de las fuentes (XSS) | Texto plano, recortado a 500 caracteres | RF-119, RF-120 |
| Q-17 | [4.6] Cambios a specs aprobadas | Se presentan y aprueban uno a uno, antes de aprobar la 003 | §5.3 |
| Q-18 | [4.7] Requisitos anuales no verificables | Cambio de temporada y relecturas del Champs, simulados en desarrollo; los ciclos en vivo, con un partido real | §6 |
| Q-19 | [4.8] Formato EARS | RF-19 antiguo pasa a regla de proceso P-1; se dividen los requisitos con dos comportamientos | P-1, RF-40, RF-41, RF-110, RF-111 |
| Q-20 | [3.1] Una parada del sistema no genera incidencias | La página de administración muestra la última consulta de cada fuente y marca las paradas | RF-112 a RF-114 |
| Q-21 | [3.2] Datos personales retirados | No se vuelven a registrar aunque las fuentes los publiquen | RF-60 |
| Q-22 | [3.3] Arranque entre temporadas | Se carga la última temporada con partidos oficiales | RF-6 |
| Q-23 | [3.4] Carga inicial larga | La web muestra lo ya cargado y trata lo demás como "sin datos"; la temporada va antes que el historial | RF-5, RF-7, RF-8 |
| Q-24 | [3.5, 3.6] Partido en vivo desaparecido, o que reaparece | Se congela con aviso discreto; si reaparece, se actualiza como el mismo partido | RF-51, RF-52, RF-90 |
| Q-25 | [3.5] Quién resuelve un partido congelado | Hugo, con la curación manual de la 002, fuera de la web | RF-51 (nota), §4 |
| Q-26 | [3.7] Respuesta vacía | Cuenta como consulta fallida | RF-46 |
| Q-27 | [3.8] Enlazar registros entre fuentes | Solo si una fuente los relaciona o Retake los une a mano (se extiende RF-131 de la 002) | RF-54, §5.3 |
| Q-28 | [3.8] Registro sin enlazar | Se retiene sin mostrar si una fuente de mayor prioridad publica ese tipo de registros | RF-55, RF-56, RF-145 |
| Q-29 | [3.9] Fuente cerrada para siempre | Sin tratamiento especial; lo ve Hugo | RF-113 |
| Q-30 | [3.10] Incidencias repetidas | Una sola entrada con número de repeticiones y hora de la última | RF-147, RF-148 |
| Q-31 | [3.11] Logos peligrosos o enormes | Solo formatos sin código ejecutable y de 1 MB como máximo | RF-68 a RF-70 |
| Q-32 | [3.12, 3.14] Sesiones | La actualización en curso termina aunque caduque la sesión; se permiten varias sesiones | RF-135 a RF-137 |
| Q-33 | [3.13] Bloqueo indefinido de la cuenta | El bloqueo es por origen, no por cuenta | RF-127, RF-129, RF-130, RF-133 |
| Q-34 | [3.15] Relecturas del historial simultáneas | Una sola en curso | RF-108, RF-109 |
| Q-35 | [3.16] Varios partidos en vivo | Si no hay tiempo para todos, el prioritario 60 s y los demás 2 min | RF-23, RF-24 |
| Q-36 | [3.16] Partido prioritario sin spec del spotlight | El que empezó antes; después, el que destaque el spotlight | RF-25, RF-26 |
| Q-37 | [3.17, 3.18] Fin de temporada | Un partido pertenece a la temporada de su evento; las páginas pasan a la nueva en 5 min | RF-73, RF-75, RF-81 |
| Q-38 | [3.19] Pestaña en segundo plano | No se actualiza; al volver, se pone al día en 5 s | RF-79 a RF-82 |
| Q-39 | [3.20] Administración sin conexión | Reglas de bloque de la 001; peticiones desactivadas | RF-115, RF-116 |
| Q-40 | [1.1, 1.2, 1.3] Plazos no medibles y "ciclo" sin definir | Los plazos pasan a ciclos máximos de consulta; se registra lo que devuelve cada consulta | RF-16, RF-18, RF-22, glosario |
| Q-41 | [1.1] Detectar el inicio de un partido | Consulta cada 60 s desde 1 h antes de su hora hasta que empieza | RF-17 |
| Q-42 | [1.4] Mapa terminado en un partido en vivo | Marcador, ganador y estadísticas del mapa, todo a 60 s | Glosario, RF-16 |
| Q-43 | [1.5] Revisión de partidos finalizados | Cada hora mientras tengan estadísticas pendientes y 7 días más. *Sustituida por C-25: una consulta al finalizar y una al día durante 3 días* | RF-19 a RF-21 |
| Q-44 | [1.6] Cuándo desaparece un partido | Tras 24 horas sin aparecer | RF-50 |
| Q-45 | [1.7] Fecha de vigencia distinta entre fuentes | Es un campo más: manda la fuente con más prioridad | RF-62 |
| Q-46 | [1.8] Cuándo hay un logo nuevo | Se compara la imagen, no la dirección | RF-66, RF-67 |
| Q-47 | [1.9] Año del pie tras un fallo | Se mantiene el año ya mostrado | RF-76, RF-78 |
| Q-48 | [1.10] Estado de la página | Scroll, foco, pestañas, carrusel y filtros; la vista no salta | RF-83, RF-84 |
| Q-49 | [1.11] Actualizar la Wiki | No incluye el historial | RF-100, RF-101 |
| Q-50 | [1.12] Resultado de una actualización pedida | Éxito, parcial o fallo, con el número de incidencias | RF-104 a RF-106 |
| Q-51 | [1.13] Contador de intentos | Por origen, con cualquier usuario; vuelve a cero con un acceso correcto o al acabar el bloqueo | RF-128, RF-131, RF-132 |
| Q-52 | [1.14] Contenido del resumen | Totales y lista de incidencias distintas por fuente | RF-151, RF-152 |
| Q-53 | [1.15] Dónde va la hora de actualización | En bloques con datos de la liga, también vacíos; no en el pie, la administración ni la demostración | RF-155, RF-156, RF-158 |
| Q-54 | [1.16] Datos que cuentan para la hora | Solo los que el bloque muestra | RF-157 |
| Q-55 | [1.17] Recuperación tras una parada | En un ciclo, solo con el estado actual | RF-27 a RF-29 |
| Q-56 | [1.18] Cambio de modo en desarrollo | Se borran los datos y se carga desde cero | RF-12, RF-13 |
| Q-57 | [1.19] Datos personales de jugadores solo históricos | Solo con las consultas del historial | RF-34 |
| Q-58 | [1.20] Número de relecturas tras el Champs | La primera antes de 1 h y siete más, a las 24 h, 48 h… 168 h | RF-31 |
| Q-59 | Conservación de una incidencia repetida (surgió al redactar) | 7 días desde su última repetición | RF-149 |

**Revisiones decididas con Hugo al redactar el plan** (2026-09-23; la spec sigue aprobada):

| # | Motivo | Decisión | Requisitos |
|---|---|---|---|
| R-1 | Revisión de las condiciones de uso (P-2): las tres fuentes exigen permiso por escrito para el acceso automático, así que RF-36 impedía cumplir RF-1 (regla P-1) | Hugo decide acceder sin permiso: API donde exista y lectura de páginas públicas donde no, como en `CDL-data-analysis`. RF-36 cambia de texto. Se añade la atribución de las fuentes en el pie (RF-160), con el cambio C-11 en la 001 | RF-36, RF-160 |

**Decisiones de la fase F0** (2026-09-23; detalle en [`source-map.md`](source-map.md) §5). No cambian el texto de ningún requisito de esta spec; afectan a cómo se cumplen:

| # | Decisión | Requisitos |
|---|---|---|
| F0-1 | La Wiki se consulta con `requests` y `action=parse` (rechaza httpx en Cloudflare); sin volcado. Nada de esquivar protecciones: si rechaza también `requests`, se aplica P-1. *Revisión (2026-09-23, cambio C-18): la Wiki rechazó también `requests`; se aplicó P-1 y Hugo decidió importar sus datos desde archivos CSV. Se retira el acceso en vivo a la Wiki (conector, adaptador TLS y `sync-once --source wiki`).* | RF-38 |
| F0-2 | Pausa de la Wiki: 10 s y espera creciente si responde `ratelimited`. BreakingPoint: 2 s. | RF-39, RF-40 |
| F0-3 | Papeles: temporada actual de BreakingPoint (su API interna JSON y sus páginas); historial y gamertags anteriores de la Wiki. La web de la CDL queda **en reserva**, sin conector: **RF-75 de la 002 (la web oficial manda en la tabla) queda incumplido** mientras tanto y la tabla sale de BreakingPoint. | RF-1, RF-36; RF-75 de la 002 |
| F0-4 | País de BreakingPoint mediante una tabla de países en la curación. | RF-22 de la 002 |
| F0-5 | En vivo y próxima temporada se construyen con la estructura conocida y se comprueban al empezar la temporada 2027. | RF-14, RF-16, RF-17, RF-57 |

### 5.2 Revisión de las fuentes (2026-09-23) · notas para el plan

Hallazgos técnicos que no son requisitos, pero que el plan debe tener en cuenta (decisión Q-15):

* **BreakingPoint.gg:** no publica `robots.txt` (404). Responde (200) a Retake identificado como tal, y la página de cada partido trae sus datos incrustados. El script `trier_breakingpoint.py` de `CDL-data-analysis` se hacía pasar por un navegador; Retake no lo hará (RF-37).
* **Web oficial de la CDL:** no publica `robots.txt` (404). Responde (200) a Retake identificado.
* **Call of Duty Esports Wiki (Fandom):** su `robots.txt` y sus páginas web están detrás de una protección anti-robots (Cloudflare, 403). Su API de MediaWiki (`api.php`) responde (200) con un User-Agent propio. Es la vía de los scripts de `CDL-data-analysis`, con una pausa de 1,5 s entre peticiones (RF-38, RF-39).
* **Credenciales:** las del administrador y las de cualquier servicio van en variables de entorno, nunca en el código (constitución §6.3).
* Las condiciones de uso de las tres fuentes se revisaron como primer paso del plan (P-2), el 2026-09-23. **BreakingPoint:** todo uso requiere su consentimiento escrito; su API se da por correo. **Fandom:** prohíbe el acceso automático sin permiso escrito, aunque el texto de la Wiki está bajo CC BY-SA. **Activision (web de la CDL):** prohíbe reproducir o distribuir su contenido sin autorización. Resultado: revisión R-1 (§5.1). El detalle está en el plan, §0.

### 5.3 Cambios a specs aprobadas

Por la decisión Q-17, cada cambio se presentó a Hugo y se aprobó por separado **antes** de aprobar esta spec. **Los diez se aprobaron y se aplicaron el 2026-09-23:** C-1 a C-3 en el §5.4 de la 001, y C-4 a C-10 en el §5.1 de la 002 (criterio 8 del §6).

| # | Spec | Cambio | Origen | Estado |
|---|---|---|---|---|
| C-1 | 001, fuera de alcance | Anotar que el inicio de sesión del administrador lo define la 003; las cuentas del público siguen fuera | Q-7 | Aprobado · aplicado |
| C-2 | 001, RF-58 | Quitar la nota de valor provisional del año (P-6); el año sale de RF-74 de la 003 | Decisión 21 | Aprobado · aplicado |
| C-3 | 001, RF-63 | Excepción: los mensajes de error recibidos de las fuentes no se traducen | Q-8 | Aprobado · aplicado |
| C-4 | 002, RF-1 | Excepción: se mantiene el calendario de la próxima temporada, sin mostrarlo, hasta que sea la actual | Q-1 | Aprobado · aplicado |
| C-5 | 002, nota de RF-3 | Indicar que la 003 cumple el cambio automático de temporada | Decisión 21 | Aprobado · aplicado |
| C-6 | 002, RF-67 | Excepción: mientras un partido está `en vivo`, vale el marcador más avanzado de cualquier fuente | Q-4 | Aprobado · aplicado |
| C-7 | 002, RF-73 | Aclarar que una identidad nueva nace del cambio del resultado combinado de las fuentes, no de la observación de una sola | Q-2 | Aprobado · aplicado |
| C-8 | 002, RF-96 | Las correcciones llegan dentro de los plazos de revisión: partidos finalizados hasta 7 días después de tener todas sus estadísticas; historial, con las relecturas de cada Champs; en ambos casos, también a petición del administrador | Decisión 6, Q-43 | Aprobado · aplicado |
| C-9 | 002, RF-131 | Extender la regla de "misma persona" a partidos, eventos y franquicias, con retención de los registros sin enlazar | Q-27, Q-28 | Aprobado · aplicado |
| C-10 | 002, RF-78 | Aclarar que una retirada de datos personales impide que vuelvan a registrarse desde las fuentes | Q-21 | Aprobado · aplicado |
| C-11 | 001, fuera de alcance | Excepción a "sin enlaces en el pie": la atribución de las fuentes de datos, con un enlace a cada una (RF-160). Surgió con la revisión R-1 | R-1 | Aprobado · aplicado (2026-09-23) |
| C-12 | 002, RF-79 | Si ninguna fuente publica el K/D, se calcula como kills ÷ deaths con 2 decimales (con 0 deaths, K/D = kills; si falta alguno, ausente). Única excepción a RF-45 junto con C-13 | Fase F0, hueco H-3 | Aprobado · aplicado (2026-09-23) |
| C-13 | 002, RF-31 | Si la fuente no publica la semana de un partido de clasificatorio, se calcula como el orden de la semana (lunes a domingo, hora de Ciudad de México) entre las semanas con partidos de ese evento | Fase F0, hueco H-5 | Aprobado · aplicado (2026-09-23) |
| C-14 | 003, RF-55 | Retener = no mostrar en la temporada actual; el historial sí usa los registros retenidos | Fase F4, T-043 | Aprobado · aplicado (2026-09-23) |
| C-15 | 003, RF-1 y glosario | La Wiki no se obtiene automáticamente: sus datos entran por archivos CSV que prepara el administrador | Bloqueo de Cloudflare a la Wiki (P-1) | Aprobado · aplicado (2026-09-23) |
| C-16 | 003, RF-4, RF-5, RF-34 | Importación manual desde la terminal (RF-4 a RF-4c): solo datos personales de jugadores del historial o de los rosters; todo o nada si falla un archivo | Ídem | Aprobado · aplicado (2026-09-23) |
| C-17 | 003, RF-18, RF-30 a RF-33 | Sin relecturas automáticas del historial; solo se registran datos de la Wiki al importar | Ídem | Aprobado · aplicado (2026-09-23) |
| C-18 | 003, RF-38, F0-1, fuera de alcance | Retake no consulta la Wiki; se retira el acceso en vivo (conector, adaptador TLS y `sync-once --source wiki`) | Ídem | Aprobado · aplicado (2026-09-23) |
| C-19 | 003, RF-100, RF-102, RF-108, RF-109, RF-113, RF-114 | Sin releer el historial desde la página de administración; la Wiki muestra su última importación y nunca aparece como parada | Ídem | Aprobado · aplicado (2026-09-23) |
| C-20 | 003, RF-89 | Los bloques con solo datos de la Wiki no muestran el aviso de datos sin actualizar | Ídem | Aprobado · aplicado (2026-09-23) |
| C-21 | 003, §3 y §6 | Casos límite y criterios de finalización pasan de las relecturas a la importación | Ídem | Aprobado · aplicado (2026-09-23) |
| C-22 | 003, RF-18a y §3 | Un equipo que la fuente ya no lista, pero que está en la tabla de la temporada, se registra como franquicia | Primera carga real, T-086: Boston Breach | Aprobado · aplicado (2026-09-24) |
| C-23 | 002, glosario, RF-117a a RF-117d y §3.11 | Equipos invitados: equipos de fuera de la CDL que juegan un evento de la CDL, con roster y jugadores (mismos datos que los de la CDL), visibles solo en sus partidos; sus estadísticas no cuentan para la temporada | Primera carga real, T-086: Minors | Aprobado · aplicado (2026-09-24) |
| C-24 | 003, nota de RF-18a, RF-18b y §3 | Los equipos que no están en la tabla se registran como invitados; sus datos y los de sus jugadores se consultan al aparecer y después una vez al mes | Ídem | Aprobado · aplicado (2026-09-24) |
| C-25 | 003, RF-19 y RF-20; 002, plazos de corrección | Revisión de partidos finalizados: una consulta al finalizar y una al día durante 3 días; ninguna más si ya eran antiguos al registrarse | Primera carga real, T-086: 281 partidos de julio en revisión horaria de 7 días | Aprobado · aplicado (2026-09-24) |
| C-26 | 003, RF-18c | Los rosters de equipos que no son de la CDL ni invitados se descartan sin anotarlos | Primera carga real, T-086: 33 rosters de 23 equipos de Challengers | Aprobado · aplicado (2026-09-24) |
| C-27 | 003, RF-12 | Al cambiar de modo en desarrollo también se borran el registro, las incidencias y los resúmenes del modo anterior | T-087: el registro de `/admin` mostraba 140 consultas simuladas con fecha de diciembre | Aprobado · aplicado (2026-09-24) |

Además, **el ajuste I-15 del plan de la 002** queda resuelto por RF-61 a RF-64. Es un plan, no una spec, así que basta con anotarlo.

### 5.4 Pendientes

No queda ningún `[NECESITA ACLARACIÓN]` abierto. Los cambios C-1 a C-27 están aprobados y aplicados. Limitación conocida, aceptada por Hugo el 2026-09-24: RF-75 de la 002 incumplido mientras la web de la CDL esté en reserva (F0-3); la tabla sale de BreakingPoint.

---

## 6. Criterios de Finalización

La spec 003 se da por terminada cuando se cumplan todas estas condiciones:

1. Hugo ha aprobado la spec, cada cambio de §5.3 y no queda ningún `[NECESITA ACLARACIÓN]` abierto.
2. Cada requisito, de RF-1 a RF-160, tiene un paso en la guía de verificación manual (constitución §5) y Hugo lo ha comprobado.
3. Los ciclos en vivo y los márgenes de pantalla (RF-16, RF-17, RF-80) se han medido con al menos un partido real en vivo.
4. Estos casos se han comprobado simulándolos en el entorno de desarrollo:
   - el cambio de temporada (RF-14, RF-15, RF-72 a RF-75);
   - la importación de los archivos de la Wiki, completa, parcial y con un archivo que falla (RF-4 a RF-4c, RF-32; cambio C-21);
   - los fallos de fuente, las respuestas vacías o a medias y los partidos desaparecidos (RF-43 a RF-53);
   - los marcadores contradictorios (RF-57 a RF-59);
   - varios partidos en vivo a la vez (RF-23 a RF-26);
   - una parada de la obtención automática (RF-27 a RF-29, RF-114).
5. En producción no aparece ningún dato de prueba, y las pruebas automáticas no consultan las fuentes reales (RF-9, RF-10).
6. Una auditoría de accesibilidad de un bloque que se actualiza solo no muestra ningún incumplimiento del nivel AA de las WCAG 2.2 (RF-94 a RF-96).
7. Se ha revisado el checklist de seguridad de la constitución (§6), en especial el acceso del administrador (RF-121 a RF-139), el texto recibido de las fuentes (RF-119, RF-120), los logos (RF-68, RF-69) y las credenciales fuera del código.
8. Se han aplicado en la 001 y en la 002 los cambios aprobados de §5.3.
9. El estado de la spec ha pasado a `Aprobado` y refleja lo que realmente se construyó, sin desviaciones (constitución §1.3).

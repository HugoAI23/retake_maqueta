# Constitution — Retake (Maqueta y Plataforma CDL Analytics & ML)

Este documento establece los principios de gobernanza, arquitectura y desarrollo para el proyecto **Retake**. Estos principios son inviolables y rigen el comportamiento de cualquier agente de Inteligencia Artificial que participe en el proyecto. Solo Hugo Portillo tiene la autoridad de modificar este documento.

---

## 1. Filosofía Central: Spec-Driven Development Puro (SDD)

El desarrollo en Retake sigue una metodología estricta de **Spec-Driven Development (SDD puro)** basada en tres pilares:

1. **Spec-First (Especificación previa obligatoria)**:
   * Queda estrictamente prohibido escribir, modificar o generar código fuente sin una especificación (*spec*) aprobada por Hugo en el directorio `specs/`.
   * Cada especificación debe contar como mínimo con:
     - **Contexto y Objetivo**: Propósito de la funcionalidad.
     - **Criterios de Aceptación**: Comportamiento funcional y no funcional esperado.
     - **Estructura de Componentes y Contratos de Datos**: Vistas, props, interfaces y modelos.
     - **Plan de Implementación**: Fases lógicas de desarrollo.
     - **Checklist de Tareas**: Tareas atómicas, ordenadas y verificables.
2. **Spec-Anchored (Alcance anclado)**:
   * Los agentes solo deben ejecutar las tareas descritas en la spec activa. Prohibido añadir funcionalidades "sorpresa", cambios cosméticos fuera de alcance o refactorizaciones no solicitadas.
3. **El Código como Fuente de Verdad y Sincronización Continua**:
   * Una vez implementada una tarea, el código funcional manda y refleja la realidad técnica del sistema.
   * Si durante la implementación se detecta un imprevisto técnico, incompatibilidad o ajuste necesario, **el agente debe actualizar la spec inmediatamente** para reflejar la realidad del código. Se prohíbe terminantemente la desincronización (*Spec Drift*).
4. **Cierre de Brechas (Gap Closing)**:
   * Ante cualquier ambigüedad, caso de borde o requisito indefinido, el agente **nunca debe asumir**. Debe detenerse y consultar a Hugo con opciones estructuradas.

---

## 2. Stack Tecnológico y Arquitectura

El stack está diseñado para ofrecer una experiencia moderna, profesional y alineada con los estándares de la industria para el portafolio de Hugo:

* **Entorno y Bundler**: **Vite** (rápido, modular y estándar actual de la industria web).
* **Base de Componentes y Vistas**: **React** (utilizando componentes funcionales limpios, estructurados y pedagógicos).
* **Estilos y Maquetación**: **Tailwind CSS** (utilizado para el sistema de diseño, diseño responsivo y consistencia visual).
* **Visualización de Datos y Dashboards**: **Bklit UI** (integrado a través del registro de shadcn/ui) para gráficas interactivas, polígonos de radar para jugadores y métricas avanzadas, aprovechando sus animaciones y estética nativa.
* **Motor de Animaciones de UI y Microinteracciones**: **Anime.js** para orquestar la dinamización de la interfaz general:
  * Animaciones de botones y estados hover/active.
  * Transiciones de entrada y efectos al hacer scroll.
  * Barras de progreso, medidores de porcentaje de ML y contadores numéricos de estadísticas.
  * Modales, paneles deslizantes y transiciones de vistas.
* **Backend y Machine Learning (cuando aplique)**: **Python** (APIs ligeras con FastAPI/Flask o scripts de procesamiento para alimentar los modelos de predicción de la CDL).
* **Base de Datos**: **PostgreSQL** para la persistencia transparente y estructurada de partidos, jugadores, predicciones y datos de usuarios.

---

## 3. Rol del Agente: Mentoría Técnica y Decisiones Estructuradas

Hugo es un desarrollador que está consolidando sus conocimientos en desarrollo web y construyendo este proyecto como pieza angular de su portafolio profesional:

1. **Didáctica y Claridad**: El agente debe explicar el *porqué* de cada solución técnica implementada, evitando generar bloques de código crípticos o sin justificación.
2. **Protocolo para Nuevas Herramientas o Librerías**: Si surge la necesidad de adoptar una herramienta, patrón o librería complementaria, el agente debe presentar una comparativa formal:
   - **Opción A vs Opción B**.
   - **Ventajas y Desventajas**.
   - **Curva de aprendizaje y complejidad**.
   - **Recomendación fundamentada**.
   - **Hugo siempre toma la decisión final**.

---

## 4. Principios Rectores de UX/UI y Diseño de Producto

El diseño de Retake debe sobresalir visualmente sin comprometer la usabilidad ni la experiencia de usuario. La Constitution no define requisitos funcionales específicos (estos van en las Specs), sino los principios rectores de diseño:

1. **Diseño Centrado en el Usuario (UCD)**: La navegación, lectura de estadísticas complejas (KD ajustado, First Bloods, control de colina) y módulos de predicción deben ser comprensibles y fluidos desde el primer contacto.
2. **Jerarquía Visual Clara y Escaneabilidad**: Uso estratégico de tamaños, pesos tipográficos, contrastes y espaciados para diferenciar de un vistazo métricas críticas, marcadores y contenido complementario.
3. **Retroalimentación Inmediata (Feedback States)**: Todo elemento con el que interactúe el usuario debe responder al instante:
   - Estados de carga (*skeletons*, spinners suaves).
   - Estados vacíos explicativos (*empty states*).
   - Indicadores visuales claros de éxito o fallo.
   - Efectos visibles de *hover*, *focus* y *active*.
4. **Microinteracciones con Propósito**: Las animaciones (con Anime.js) deben guiar la vista y enriquecer la inmersión competitiva de la plataforma; nunca deben ralentizar la navegación ni distraer al usuario.
5. **Consistencia del Sistema de Diseño (Design System)**: Coherencia estricta en paleta de colores, sombras, radios de borde y tipografía a través de todas las vistas.
6. **Accesibilidad y Adaptabilidad Responsiva**: Contraste adecuado para lectura en entornos oscuros (Dark Theme de esports) y comportamiento impecable tanto en dispositivos móviles como en pantallas de escritorio.

---

## 5. Protocolo de Pruebas Manuales y Calidad

Dado el carácter del proyecto y el enfoque de aprendizaje:

1. **Guías de Verificación Manual Paso a Paso**: Tras completar cualquier tarea o componente, el agente debe proporcionar a Hugo una guía explícita para validar el trabajo en el navegador:
   - **Paso 1**: Archivo o vista a abrir en el servidor de desarrollo.
   - **Paso 2**: Acción interactiva a realizar (ej: hacer clic en un filtro, interactuar con una gráfica de Bklit UI).
   - **Paso 3**: Comportamiento o resultado visual esperado.
2. **Bitácora y Gestión de Bugs**: Cualquier fallo o anomalía detectada debe documentarse con causa raíz, impacto y solución aplicada.

---

## 6. Seguridad Proactiva

El agente asume el rol de asesor de seguridad para garantizar que la plataforma esté protegida desde sus cimientos:

1. **Sanitización de Entradas**: Validación estricta y escape de datos para prevenir vulnerabilidades XSS (Cross-Site Scripting) en formularios de votación, predicciones o comentarios.
2. **Consultas Seguras**: Uso exclusivo de consultas parametrizadas u ORMs seguros para evitar Inyecciones SQL al interactuar con PostgreSQL.
3. **Manejo Seguro de Credenciales**: Nunca registrar claves de API, secretos o credenciales en el código fuente ni en el frontend. Uso estricto de variables de entorno (`.env`).
4. **Checklist de Seguridad**: El agente verificará estos vectores antes de dar por concluida cualquier spec.

---

## 7. Convenciones de Idioma y Estilo de Código

1. **Código Fuente Técnico**: Nombres de variables, funciones, componentes, clases, interfaces, rutas y archivos deben escribirse en **inglés** (ej: `PlayerStatsCard`, `calculateAdjustedKd`, `matchPredictionList`).
2. **Documentación y Diálogo**: Comentarios en el código, redacción de especificaciones, planes de implementación y explicaciones hacia Hugo deben escribirse en **español**.
3. **Preparación para Internacionalización (i18n)**: Los textos de la interfaz deben estar estructurados de modo que permitan una traducción fluida entre español e inglés en el futuro.

---

## 8. Restricciones Estrictas de Git y Control de Versiones

Hugo tiene el control absoluto del repositorio y su historial:

1. **Permisos Exclusivos de Consulta**: Los agentes de IA **SOLO pueden ejecutar comandos de lectura**:
   - `git status`
   - `git diff`
   - `git log`
2. **Operaciones Prohibidas para el Agente**: Queda estrictamente prohibido ejecutar `git add`, `git commit`, `git push`, `git checkout`, `git branch` o cualquier comando que altere el estado del repositorio.
3. **Sugerencias de Commits**: Tras finalizar y verificar una tarea, el agente sugerirá a Hugo el mensaje de commit semántico correspondiente (ej: `feat: add player radar chart using bklit ui`) para que Hugo lo ejecute manualmente si así lo decide.

/**
 * Textos de la interfaz en español (RF-63, RF-70).
 * Los nombres propios de la liga (franquicias, gamertags, eventos, mapas y
 * modos) NO se incluyen aquí: se muestran tal como llegan en los datos (RF-72).
 */
export default {
  app: {
    name: 'Retake',
    skipToContent: 'Saltar al contenido',
  },
  sections: {
    home: 'Inicio',
    matches: 'Partidos',
    teams: 'Equipos',
    players: 'Jugadores',
    tournaments: 'Torneos',
    standings: 'Posiciones',
    news: 'Noticias',
    mlModels: 'Modelos de ML',
  },
  blocks: {
    ticker: 'Cinta de marcadores',
    spotlight: 'Spotlight',
    news: 'Noticias',
    matchGrid: 'Próximos partidos',
  },
  nav: {
    mainLabel: 'Navegación principal',
    panelLabel: 'Menú de secciones',
    openMenu: 'Abrir menú',
    closeMenu: 'Cerrar menú',
    mlBadge: 'IA',
  },
  logo: {
    homeLink: 'Retake, ir a Inicio',
  },
  language: {
    label: 'Idioma',
  },
  status: {
    comingSoon: 'Próximamente',
    loading: 'Cargando…',
    loadError: 'No se pudo cargar este contenido.',
    retry: 'Reintentar',
    retryBlock: 'Reintentar: {{block}}',
    offline: 'Sin conexión. Mostramos lo que ya estaba cargado.',
  },
  home: {
    heading: 'Retake: estadísticas y predicciones de la Call of Duty League',
  },
  notFound: {
    title: 'Página no encontrada',
    message: 'La dirección que buscas no existe en Retake.',
    backHome: 'Volver a Inicio',
  },
  footer: {
    disclaimer:
      'Proyecto escolar sin afiliación oficial con la Call of Duty League.',
    season: 'Temporada {{year}}',
    dataFrom: 'Datos de',
    wikiLicense: 'Texto de la Wiki con licencia CC BY-SA 3.0',
  },
  live: {
    lastUpdated: 'Actualizado: {{when}}',
    neverUpdated: 'Sin actualizar todavía',
    stale: 'Estos datos pueden no estar al día.',
  },
  admin: {
    title: 'Administración',
    logout: 'Cerrar sesión',
    signedInAs: 'Sesión de {{username}}',
    login: {
      heading: 'Acceso de administración',
      username: 'Usuario',
      password: 'Contraseña',
      submit: 'Entrar',
      wrong: 'Usuario o contraseña incorrectos.',
      blocked: 'Demasiados intentos fallidos desde este dispositivo o red. Vuelve a intentarlo dentro de 15 minutos.',
      error: 'No se ha podido entrar. Inténtalo de nuevo.',
      unreachable: 'No se ha podido conectar con el servidor. Inténtalo de nuevo en un momento.',
    },
    sources: {
      heading: 'Estado de las fuentes',
      blockName: 'Estado de las fuentes',
      name: { bp: 'BreakingPoint.gg', wiki: 'Call of Duty Esports Wiki', cdl: 'Web oficial de la CDL' },
      lastAttempt: 'Última consulta',
      lastSuccess: 'Última consulta con éxito',
      lastImport: 'Última importación',
      never: 'Nunca',
      stopped: 'Parada',
      working: 'En funcionamiento',
      refresh: 'Actualizar {{source}}',
      offline: 'Sin conexión: no se pueden pedir actualizaciones.',
      reason: {
        wiki: 'La Wiki no se consulta: sus datos se importan con «uv run retake import-wiki-csv».',
        cdl: 'La web oficial de la CDL está en reserva, sin conector.',
      },
    },
    request: {
      pending: 'Pendiente',
      running: 'En curso',
      success: 'Éxito',
      partial: 'Parcial',
      failure: 'Fallo',
      forbidden: 'No permitida',
      alreadyRunning: 'Ya había una actualización en curso de esta fuente.',
      incidents: 'Incidencias: {{count}}',
      viewLog: 'Ver en el registro',
      failed: 'No se ha podido pedir la actualización.',
    },
    log: {
      heading: 'Registro de los últimos 7 días',
      blockName: 'Registro',
      source: 'Fuente',
      all: 'Todas',
      runs: 'Consultas',
      incidents: 'Incidencias',
      repetitions: '{{count}} veces',
      lastAt: 'Última vez: {{when}}',
      empty: 'Sin entradas.',
      previous: 'Anteriores',
      next: 'Siguientes',
    },
    summaries: {
      heading: 'Resúmenes diarios',
      blockName: 'Resúmenes diarios',
      empty: 'Sin resúmenes en los últimos 7 días.',
      totals: 'Incidencias: {{incidents}} · Consultas fallidas: {{failed}} · Datos rechazados: {{rejected}}',
      bySource: '{{source}}: consultas fallidas: {{failed}} · datos rechazados: {{rejected}}',
      system: 'Retake (acceso y proceso)',
    },
  },
  league: {
    matchStatus: {
      scheduled: 'programado',
      live: 'en vivo',
      finished: 'finalizado',
    },
    notAvailable: 'No disponible',
    noRole: 'Sin rol',
    statsPending: 'Estadísticas pendientes',
    // Etiquetas añadidas al aprobar la spec 002 (§2.9). Las siglas DQ, SMG y AR
    // no pasan por el diccionario: se muestran igual en todos los idiomas (RF-125).
    toBeDecided: 'Por definir',
    winnerOf: 'Ganador de {{match}}',
    loserOf: 'Perdedor de {{match}}',
    notPlayed: 'No jugado',
    corrected: 'Corregido',
    freeAgent: 'Agente libre',
    standingsUnavailable: 'La tabla de posiciones todavía no está disponible',
    phase: {
      week: 'semana',
      group: 'grupo',
      winnersBracket: 'winners bracket',
      losersBracket: 'losers bracket',
      grandFinal: 'gran final',
    },
  },
}

/**
 * Textos de la interfaz en inglés (RF-63, RF-70).
 * Debe tener exactamente las mismas claves que es.js (lo comprueba dictionaries.test.js).
 */
export default {
  app: {
    name: 'Retake',
    skipToContent: 'Skip to content',
  },
  sections: {
    home: 'Home',
    matches: 'Matches',
    teams: 'Teams',
    players: 'Players',
    tournaments: 'Tournaments',
    standings: 'Standings',
    news: 'News',
    mlModels: 'ML Models',
  },
  blocks: {
    ticker: 'Score ticker',
    spotlight: 'Spotlight',
    news: 'News',
    matchGrid: 'Upcoming matches',
  },
  nav: {
    mainLabel: 'Main navigation',
    panelLabel: 'Sections menu',
    openMenu: 'Open menu',
    closeMenu: 'Close menu',
    mlBadge: 'AI',
  },
  logo: {
    homeLink: 'Retake, go to Home',
  },
  language: {
    label: 'Language',
  },
  status: {
    comingSoon: 'Coming soon',
    loading: 'Loading…',
    loadError: 'This content could not be loaded.',
    retry: 'Retry',
    retryBlock: 'Retry: {{block}}',
    offline: 'You are offline. Showing what was already loaded.',
  },
  home: {
    heading: 'Retake: Call of Duty League stats and predictions',
  },
  notFound: {
    title: 'Page not found',
    message: 'The address you are looking for does not exist on Retake.',
    backHome: 'Back to Home',
  },
  footer: {
    disclaimer:
      'School project with no official affiliation with the Call of Duty League.',
    season: '{{year}} season',
  },
  league: {
    matchStatus: {
      scheduled: 'scheduled',
      live: 'live',
      finished: 'final',
    },
    notAvailable: 'Not available',
    noRole: 'No role',
    statsPending: 'Stats pending',
    phase: {
      week: 'week',
      group: 'group',
      winnersBracket: 'winners bracket',
      losersBracket: 'losers bracket',
      final: 'final',
    },
  },
}

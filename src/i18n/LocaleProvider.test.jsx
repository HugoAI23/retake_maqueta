import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { describe, expect, it } from 'vitest'
import { renderWithProviders } from '../test/renderWithProviders.jsx'
import { LanguageSwitcher } from './LanguageSwitcher.jsx'
import { LOCALE_STORAGE_KEY } from './localeStorage.js'

// Componente con estado interno: si el cambio de idioma lo desmontara,
// el contador volvería a 0 (RF-64).
function StatefulChild() {
  const { t } = useTranslation()
  const [count, setCount] = useState(0)
  return (
    <div>
      <p>{t('sections.players')}</p>
      <button type="button" onClick={() => setCount((c) => c + 1)}>
        contador {count}
      </button>
    </div>
  )
}

describe('LocaleProvider y LanguageSwitcher (RF-59, RF-63 a RF-65, RF-79)', () => {
  it('cambia los textos, guarda la elección y actualiza lang sin desmontar la página', async () => {
    const user = userEvent.setup()
    renderWithProviders(
      <>
        <LanguageSwitcher />
        <StatefulChild />
      </>,
    )

    await user.click(screen.getByRole('button', { name: /contador/ }))
    expect(screen.getByRole('button', { name: 'contador 1' })).toBeInTheDocument()
    expect(screen.getByText('Jugadores')).toBeInTheDocument()
    expect(document.documentElement.lang).toBe('es')

    await user.click(screen.getByRole('button', { name: 'English' }))

    expect(screen.getByText('Players')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'contador 1' })).toBeInTheDocument()
    expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBe('en')
    expect(document.documentElement.lang).toBe('en')
  })

  it('indica la opción activa y nombra cada opción en su idioma', () => {
    renderWithProviders(<LanguageSwitcher />, { locale: 'en' })
    const group = screen.getByRole('group', { name: 'Language' })
    expect(group).toBeInTheDocument()
    const english = screen.getByRole('button', { name: 'English' })
    const spanish = screen.getByRole('button', { name: 'Español' })
    expect(english).toHaveAttribute('aria-pressed', 'true')
    expect(spanish).toHaveAttribute('aria-pressed', 'false')
    expect(spanish).toHaveAttribute('lang', 'es')
  })
})

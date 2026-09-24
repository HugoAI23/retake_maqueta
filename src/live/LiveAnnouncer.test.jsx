import { act, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { LiveAnnouncerProvider, useAnnouncer } from './LiveAnnouncer.jsx'

let announce
function Probe() {
  announce = useAnnouncer()
  return null
}

describe('anuncios accesibles (T-073; RF-94 a RF-96)', () => {
  it('anuncia sin interrumpir los cambios de los datos en vivo', () => {
    render(<LiveAnnouncerProvider><Probe /></LiveAnnouncerProvider>)
    const region = screen.getByRole('status')
    expect(region).toHaveAttribute('aria-live', 'polite')
    act(() => announce('Uno 2 - 1 Dos', { dataset: 'live' }))
    expect(region).toHaveTextContent('Uno 2 - 1 Dos')
  })

  it('nunca anuncia los cambios del resto de datos', () => {
    render(<LiveAnnouncerProvider><Probe /></LiveAnnouncerProvider>)
    act(() => announce('Nueva tabla de posiciones', { dataset: 'standings' }))
    expect(screen.getByRole('status')).toHaveTextContent('')
  })
})

import { act, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { renderWithProviders } from '../test/renderWithProviders.jsx'
import { AsyncBlock } from './AsyncBlock.jsx'
import { BlockError } from './BlockError.jsx'
import { BlockSkeleton } from './BlockSkeleton.jsx'
import { BlockSlot } from './BlockSlot.jsx'

describe('BlockSlot sin contenido (RF-38, RF-39)', () => {
  it('muestra el nombre y "Próximamente" y nunca llama a la carga', () => {
    const load = vi.fn()
    renderWithProviders(<BlockSlot block={{ id: 'spotlight', hasContent: false }} load={load} />)
    expect(screen.getByRole('heading', { name: 'Spotlight' })).toBeInTheDocument()
    expect(screen.getByText('Próximamente')).toBeInTheDocument()
    expect(screen.queryByTestId('block-skeleton')).not.toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(load).not.toHaveBeenCalled()
  })
})

describe('BlockSkeleton (RF-40)', () => {
  it('se anuncia como cargando', () => {
    renderWithProviders(<BlockSkeleton />)
    expect(screen.getByRole('status')).toHaveAttribute('aria-busy', 'true')
    expect(screen.getByText('Cargando…')).toBeInTheDocument()
  })
})

describe('BlockError (RF-41, RF-44, RF-79)', () => {
  it('muestra el aviso y un "Reintentar" con el nombre del bloque', async () => {
    const onRetry = vi.fn()
    renderWithProviders(<BlockError blockName="Spotlight" onRetry={onRetry} />)
    expect(screen.getByRole('alert')).toHaveTextContent('No se pudo cargar este contenido.')
    const button = screen.getByRole('button', { name: 'Reintentar: Spotlight' })
    expect(button).toHaveTextContent('Reintentar')
    await userEvent.click(button)
    expect(onRetry).toHaveBeenCalledTimes(1)
  })
})

describe('AsyncBlock (RF-40, RF-41, RF-47, RF-48)', () => {
  it('dos bloques son independientes: uno en error no afecta al otro', async () => {
    let failA
    let resolveB
    const loadA = () => new Promise((_r, reject) => (failA = reject))
    const loadB = () => new Promise((resolve) => (resolveB = resolve))
    renderWithProviders(
      <>
        <AsyncBlock blockName="A" load={loadA} renderContent={(d) => <p>A: {d}</p>} />
        <AsyncBlock blockName="B" load={loadB} renderContent={(d) => <p>B: {d}</p>} />
      </>,
    )
    expect(screen.getAllByRole('status')).toHaveLength(2)

    await act(async () => failA(new Error('x')))
    await act(async () => resolveB('listo'))

    expect(screen.getByRole('button', { name: 'Reintentar: A' })).toBeInTheDocument()
    expect(screen.getByText('B: listo')).toBeInTheDocument()
    // Éxito sin avisos adicionales (RF-47): solo queda el error de A.
    expect(screen.getAllByRole('alert')).toHaveLength(1)
  })
})

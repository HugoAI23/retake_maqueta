import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { describe, expect, it, vi } from 'vitest'
import { renderWithProviders } from '../test/renderWithProviders.jsx'
import { DataTable } from './DataTable.jsx'

const rows = [
  { id: 'a', position: 1, name: 'Alfa', points: 30 },
  { id: 'b', position: 2, name: 'Beta', points: 50 },
  { id: 'c', position: 3, name: 'Gamma', points: null },
]

const columns = [
  { id: 'position', header: 'Pos.', sortKind: 'ascending', value: (r) => r.position, render: (r) => r.position, sticky: true },
  { id: 'name', header: 'Equipo', sortKind: 'text', value: (r) => r.name, render: (r) => r.name, sticky: true, rowHeader: true },
  { id: 'points', header: 'Puntos', sortKind: 'descending', value: (r) => r.points, render: (r) => r.points ?? 'No disponible', align: 'end' },
  { id: 'logo', header: 'Logo', sortKind: null, value: () => null, render: () => '—' },
]

/** Tabla controlada como la usará una página: el estado del orden vive fuera. */
function Harness({ initial = null, onSortChange }) {
  const [sortState, setSortState] = useState(initial)
  return (
    <DataTable
      caption="Tabla de prueba"
      columns={columns}
      rows={rows}
      rowKey={(r) => r.id}
      sortState={sortState}
      onSortChange={(next) => {
        setSortState(next)
        onSortChange?.(next)
      }}
    />
  )
}

const bodyRowNames = () =>
  screen.getAllByRole('row').slice(1).map((row) => within(row).getByRole('rowheader').textContent)

describe('DataTable: estructura (spec 004, RF-1, RF-36, RF-36a; D-8)', () => {
  it('es una tabla con título, una cabecera por columna y cabecera de fila', () => {
    renderWithProviders(<Harness />)
    const table = screen.getByRole('table', { name: 'Tabla de prueba' })
    const headers = within(table).getAllByRole('columnheader')
    expect(headers.map((h) => h.getAttribute('scope'))).toEqual(['col', 'col', 'col', 'col'])
    expect(headers.map((h) => h.textContent)).toEqual([
      expect.stringContaining('Pos.'),
      expect.stringContaining('Equipo'),
      expect.stringContaining('Puntos'),
      'Logo',
    ])
    const rowHeaders = within(table).getAllByRole('rowheader')
    expect(rowHeaders.map((h) => h.textContent)).toEqual(['Alfa', 'Beta', 'Gamma'])
    expect(rowHeaders.every((h) => h.getAttribute('scope') === 'row')).toBe(true)
  })

  it('muestra las filas en el orden que recibe cuando no hay orden elegido (RF-2)', () => {
    renderWithProviders(<Harness />)
    expect(bodyRowNames()).toEqual(['Alfa', 'Beta', 'Gamma'])
  })

  it('aplica el orden por defecto de la sección si lo recibe', () => {
    renderWithProviders(
      <DataTable
        caption="Tabla"
        columns={columns}
        rows={[...rows].reverse()}
        rowKey={(r) => r.id}
        defaultOrder={(a, b) => a.position - b.position}
        sortState={null}
        onSortChange={() => {}}
      />,
    )
    expect(bodyRowNames()).toEqual(['Alfa', 'Beta', 'Gamma'])
  })
})

describe('DataTable: orden (spec 004, RF-3 a RF-6, RF-37; D-9)', () => {
  it('las cabeceras ordenables son botones; las excluidas, no', () => {
    renderWithProviders(<Harness />)
    const table = screen.getByRole('table')
    expect(within(table).getAllByRole('button').map((b) => b.textContent)).toEqual([
      expect.stringContaining('Pos.'),
      expect.stringContaining('Equipo'),
      expect.stringContaining('Puntos'),
    ])
    expect(within(screen.getAllByRole('columnheader')[3]).queryByRole('button')).toBeNull()
  })

  it('con el puntero recorre el ciclo mejor → peor → por defecto y reordena', async () => {
    const user = userEvent.setup()
    const onSortChange = vi.fn()
    renderWithProviders(<Harness onSortChange={onSortChange} />)
    const points = screen.getByRole('button', { name: /Puntos/ })

    await user.click(points)
    expect(onSortChange).toHaveBeenLastCalledWith({ columnId: 'points', direction: 'best' })
    expect(bodyRowNames()).toEqual(['Beta', 'Alfa', 'Gamma'])

    await user.click(points)
    expect(onSortChange).toHaveBeenLastCalledWith({ columnId: 'points', direction: 'worst' })
    expect(bodyRowNames()).toEqual(['Alfa', 'Beta', 'Gamma'])

    await user.click(points)
    expect(onSortChange).toHaveBeenLastCalledWith(null)
    expect(bodyRowNames()).toEqual(['Alfa', 'Beta', 'Gamma'])
  })

  it('con el teclado ordena con las mismas reglas (Intro y Espacio)', async () => {
    const user = userEvent.setup()
    const onSortChange = vi.fn()
    renderWithProviders(<Harness onSortChange={onSortChange} />)
    await user.tab()
    expect(screen.getByRole('button', { name: /Pos\./ })).toHaveFocus()
    await user.tab()
    await user.tab()
    expect(screen.getByRole('button', { name: /Puntos/ })).toHaveFocus()
    await user.keyboard('{Enter}')
    expect(onSortChange).toHaveBeenLastCalledWith({ columnId: 'points', direction: 'best' })
    await user.keyboard(' ')
    expect(onSortChange).toHaveBeenLastCalledWith({ columnId: 'points', direction: 'worst' })
  })

  it('indica al lector la columna y el sentido con aria-sort y con texto', async () => {
    const user = userEvent.setup()
    renderWithProviders(<Harness />)
    const headers = () => screen.getAllByRole('columnheader')
    expect(headers().some((h) => h.hasAttribute('aria-sort'))).toBe(false)

    // Puntos: «mayor es mejor», así que de mejor a peor es descendente.
    await user.click(screen.getByRole('button', { name: /Puntos/ }))
    expect(headers()[2]).toHaveAttribute('aria-sort', 'descending')
    expect(screen.getByRole('button', { name: /Puntos/ })).toHaveAccessibleName('Puntos, ordenada de mejor a peor')
    expect(headers().filter((h) => h.hasAttribute('aria-sort'))).toHaveLength(1)

    await user.click(screen.getByRole('button', { name: /Puntos/ }))
    expect(headers()[2]).toHaveAttribute('aria-sort', 'ascending')
    expect(screen.getByRole('button', { name: /Puntos/ })).toHaveAccessibleName('Puntos, ordenada de peor a mejor')

    // Posición: «menor es mejor», así que de mejor a peor es ascendente.
    await user.click(screen.getByRole('button', { name: /Pos\./ }))
    expect(headers()[0]).toHaveAttribute('aria-sort', 'ascending')
    expect(headers()[2]).not.toHaveAttribute('aria-sort')
  })

  it('la cabecera ordenable ofrece la acción de ordenar en inglés también', () => {
    renderWithProviders(<Harness initial={{ columnId: 'name', direction: 'best' }} />, { locale: 'en' })
    expect(screen.getByRole('button', { name: /Equipo/ })).toHaveAccessibleName('Equipo, sorted best to worst')
    expect(screen.getByRole('button', { name: /Puntos/ })).toHaveAttribute('title', 'Sort by Puntos')
  })
})

describe('DataTable: desplazamiento y estados (spec 004, RF-12, RF-13, RF-38)', () => {
  it('la tabla se desplaza dentro de su caja y las columnas fijas son sticky', () => {
    renderWithProviders(<Harness />)
    const table = screen.getByRole('table')
    expect(table.parentElement).toHaveClass('overflow-x-auto')
    // Posicionada: así los textos para el lector (sr-only, en posición absoluta) quedan dentro
    // de la caja y no agrandan la página (visto en la F5 a 320 px).
    expect(table.parentElement).toHaveClass('relative')
    const [pos, team, points] = screen.getAllByRole('columnheader')
    expect(pos).toHaveClass('sticky')
    expect(team).toHaveClass('sticky')
    expect(points).not.toHaveClass('sticky')
    const firstRow = screen.getAllByRole('row')[1]
    expect(within(firstRow).getByRole('rowheader')).toHaveClass('sticky')
  })

  it('las cabeceras ordenables tienen los estados hover y active de la 001', () => {
    renderWithProviders(<Harness />)
    const button = screen.getByRole('button', { name: /Puntos/ })
    expect(button.className).toMatch(/hover:/)
    expect(button.className).toMatch(/active:/)
    expect(button.className).toMatch(/min-h-11/)
  })
})

import { act, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MAX_ANIMATION_MS, motionPresets } from './motionPresets.js'
import { MotionProvider, useReducedMotion } from './MotionProvider.jsx'

function Probe() {
  return <p>{useReducedMotion() ? 'reducir' : 'normal'}</p>
}

describe('motionPresets (RF-87)', () => {
  it.each(Object.entries(motionPresets))('%s dura %o como máximo 300 ms', (_name, preset) => {
    expect(preset.duration).toBeLessThanOrEqual(MAX_ANIMATION_MS)
  })
})

describe('MotionProvider (RF-88)', () => {
  const original = window.matchMedia
  afterEach(() => {
    window.matchMedia = original
  })

  it('refleja la preferencia del sistema y reacciona a su cambio', () => {
    let listener
    const media = {
      matches: false,
      addEventListener: (_type, fn) => {
        listener = fn
      },
      removeEventListener: vi.fn(),
    }
    window.matchMedia = vi.fn(() => media)

    render(
      <MotionProvider>
        <Probe />
      </MotionProvider>,
    )
    expect(screen.getByText('normal')).toBeInTheDocument()

    act(() => {
      media.matches = true
      listener()
    })
    expect(screen.getByText('reducir')).toBeInTheDocument()
  })
})

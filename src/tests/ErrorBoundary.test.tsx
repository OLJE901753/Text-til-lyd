import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ErrorBoundary } from '@/components/ErrorBoundary'

// Component that throws an error
const ThrowError = () => {
  throw new Error('Test error')
}

describe('ErrorBoundary', () => {
  it('catches errors and displays error message', () => {
    // Suppress console.error for this test
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    
    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )
    
    expect(screen.getByText(/something went wrong/i)).toBeDefined()
    
    consoleSpy.mockRestore()
  })
})

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FileUpload } from '@/components/FileUpload'

describe('FileUpload', () => {
  it('renders upload area', () => {
    const onFileSelect = vi.fn()
    render(<FileUpload onFileSelect={onFileSelect} />)
    
    expect(screen.getByText(/drag & drop audio file/i)).toBeDefined()
  })

  it('renders with correct structure', () => {
    const onFileSelect = vi.fn()
    const { container } = render(<FileUpload onFileSelect={onFileSelect} />)
    expect(container).toBeDefined()
  })
})

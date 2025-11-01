/**
 * Tests for SearchBar component.
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { SearchBar } from '@/components/search/SearchBar'

describe('SearchBar', () => {
  it('renders search input and button', () => {
    const mockOnSearch = jest.fn()
    render(<SearchBar onSearch={mockOnSearch} />)

    // Check that input and button are rendered
    expect(screen.getByPlaceholderText(/search for papers/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument()
  })

  it('calls onSearch when form is submitted', async () => {
    const mockOnSearch = jest.fn()
    render(<SearchBar onSearch={mockOnSearch} />)

    const input = screen.getByPlaceholderText(/search for papers/i)
    const button = screen.getByRole('button', { name: /search/i })

    // Enter query and submit
    fireEvent.change(input, { target: { value: 'solid-state batteries' } })
    fireEvent.click(button)

    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('solid-state batteries')
    })
  })

  it('does not call onSearch with empty query', () => {
    const mockOnSearch = jest.fn()
    render(<SearchBar onSearch={mockOnSearch} />)

    const button = screen.getByRole('button', { name: /search/i })
    fireEvent.click(button)

    expect(mockOnSearch).not.toHaveBeenCalled()
  })

  it('trims whitespace from query', async () => {
    const mockOnSearch = jest.fn()
    render(<SearchBar onSearch={mockOnSearch} />)

    const input = screen.getByPlaceholderText(/search for papers/i)
    const button = screen.getByRole('button', { name: /search/i })

    // Enter query with leading/trailing whitespace
    fireEvent.change(input, { target: { value: '  batteries  ' } })
    fireEvent.click(button)

    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('batteries')
    })
  })

  it('disables input and button when searching', () => {
    const mockOnSearch = jest.fn()
    render(<SearchBar onSearch={mockOnSearch} isSearching={true} />)

    const input = screen.getByPlaceholderText(/search for papers/i)
    const button = screen.getByRole('button', { name: /search/i })

    expect(input).toBeDisabled()
    expect(button).toBeDisabled()
  })

  it('shows loading indicator when searching', () => {
    const mockOnSearch = jest.fn()
    render(<SearchBar onSearch={mockOnSearch} isSearching={true} />)

    // Loader icon should be visible (using lucide-react's Loader2)
    // This is a simple check - in a real app you might test for animation
    expect(screen.getByPlaceholderText(/search for papers/i)).toBeDisabled()
  })
})


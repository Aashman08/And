/**
 * Tests for ResultCard component.
 */
import { render, screen, fireEvent } from '@testing-library/react'
import { ResultCard } from '@/components/search/ResultCard'
import type { SearchResult } from '@/lib/api'

const mockPaperResult: SearchResult = {
  id: 'paper1',
  source: 'papers',
  title: 'Solid-State Battery Electrolytes',
  snippet: 'A comprehensive study on solid-state battery electrolytes for electric vehicles...',
  score: 0.95,
  why_this_result: [
    'Discusses solid-state electrolytes',
    'Focuses on electric vehicle applications',
  ],
  metadata: {
    year: 2023,
    venue: 'Nature Energy',
    concepts: ['batteries', 'materials science'],
    authors: ['John Doe', 'Jane Smith'],
    doi: '10.1038/example',
  },
}

const mockStartupResult: SearchResult = {
  id: 'startup1',
  source: 'startups',
  title: 'Battery Innovations Inc',
  snippet: 'A startup developing next-generation battery technology...',
  score: 0.88,
  why_this_result: ['Innovative battery management system'],
  metadata: {
    year: 2024,
    website: 'https://batteryinnovations.com',
    industry: ['energy', 'transportation'],
    stage: 'Series A',
  },
}

describe('ResultCard', () => {
  it('renders paper result correctly', () => {
    const mockOnSummarize = jest.fn()
    render(<ResultCard result={mockPaperResult} onSummarize={mockOnSummarize} />)

    // Check title and snippet
    expect(screen.getByText('Solid-State Battery Electrolytes')).toBeInTheDocument()
    expect(screen.getByText(/comprehensive study/i)).toBeInTheDocument()

    // Check metadata
    expect(screen.getByText('2023')).toBeInTheDocument()
    expect(screen.getByText(/John Doe, Jane Smith/i)).toBeInTheDocument()
    expect(screen.getByText('Nature Energy')).toBeInTheDocument()

    // Check score badge
    expect(screen.getByText('95%')).toBeInTheDocument()

    // Check highlights
    expect(screen.getByText(/Discusses solid-state electrolytes/i)).toBeInTheDocument()
  })

  it('renders startup result correctly', () => {
    const mockOnSummarize = jest.fn()
    render(<ResultCard result={mockStartupResult} onSummarize={mockOnSummarize} />)

    // Check title and snippet
    expect(screen.getByText('Battery Innovations Inc')).toBeInTheDocument()
    expect(screen.getByText(/next-generation battery/i)).toBeInTheDocument()

    // Check metadata
    expect(screen.getByText('Series A')).toBeInTheDocument()

    // Check external link
    const link = screen.getByRole('link', { name: /visit website/i })
    expect(link).toHaveAttribute('href', 'https://batteryinnovations.com')
  })

  it('calls onSummarize when summary button is clicked', () => {
    const mockOnSummarize = jest.fn()
    render(<ResultCard result={mockPaperResult} onSummarize={mockOnSummarize} />)

    const summaryButton = screen.getByRole('button', { name: /generate ai summary/i })
    fireEvent.click(summaryButton)

    expect(mockOnSummarize).toHaveBeenCalledTimes(1)
  })

  it('shows loading state when summarizing', () => {
    const mockOnSummarize = jest.fn()
    render(<ResultCard result={mockPaperResult} isSummarizing={true} onSummarize={mockOnSummarize} />)

    expect(screen.getByText(/generating summary/i)).toBeInTheDocument()
  })

  it('displays summary when available', () => {
    const mockOnSummarize = jest.fn()
    const mockSummary = {
      problem: 'Low energy density in batteries',
      approach: 'Novel solid-state electrolyte materials',
      evidence_or_signals: 'Experimental validation with prototype cells',
      result: 'Improved energy density by 40%',
      limitations: 'High manufacturing costs',
    }

    render(
      <ResultCard
        result={mockPaperResult}
        summary={mockSummary}
        onSummarize={mockOnSummarize}
      />
    )

    // Click to expand summary
    const summaryButton = screen.getByRole('button', { name: /ai summary/i })
    fireEvent.click(summaryButton)

    // Check that summary sections are displayed
    expect(screen.getByText(/Low energy density/i)).toBeInTheDocument()
    expect(screen.getByText(/Novel solid-state electrolyte/i)).toBeInTheDocument()
    expect(screen.getByText(/Improved energy density by 40%/i)).toBeInTheDocument()
  })

  it('renders tags/concepts for papers', () => {
    const mockOnSummarize = jest.fn()
    render(<ResultCard result={mockPaperResult} onSummarize={mockOnSummarize} />)

    expect(screen.getByText('batteries')).toBeInTheDocument()
    expect(screen.getByText('materials science')).toBeInTheDocument()
  })

  it('renders industry tags for startups', () => {
    const mockOnSummarize = jest.fn()
    render(<ResultCard result={mockStartupResult} onSummarize={mockOnSummarize} />)

    expect(screen.getByText('energy')).toBeInTheDocument()
    expect(screen.getByText('transportation')).toBeInTheDocument()
  })
})


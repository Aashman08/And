'use client'

import { useState } from 'react'
import { SearchBar } from '@/components/search/SearchBar'
import { Facets } from '@/components/search/Facets'
import { ResultCard } from '@/components/search/ResultCard'
import { searchDocuments, summarizeDocuments, type SearchResult, type SearchFilters, type SummarySection } from '@/lib/api'
import { Loader2, AlertCircle } from 'lucide-react'

export default function HomePage() {
  // Search state
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState<SearchFilters>({})
  const [startups, setStartups] = useState<SearchResult[]>([])
  const [papers, setPapers] = useState<SearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)

  // Summarization state
  const [summaries, setSummaries] = useState<Record<string, SummarySection>>({})
  const [summarizingIds, setSummarizingIds] = useState<Set<string>>(new Set())

  /**
   * Handle search submission
   */
  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return

    setQuery(searchQuery)
    setIsSearching(true)
    setSearchError(null)

    try {
      const response = await searchDocuments({
        query: searchQuery,
        filters,
        limit: 20,
      })

      setStartups(response.startups)  // Top 10 from Tavily
      setPapers(response.papers)      // Top 20 from database
    } catch (error) {
      console.error('Search failed:', error)
      setSearchError(error instanceof Error ? error.message : 'Search failed')
    } finally {
      setIsSearching(false)
    }
  }

  /**
   * Handle filter changes
   */
  const handleFilterChange = (newFilters: SearchFilters) => {
    setFilters(newFilters)
    // Re-run search if query exists
    if (query) {
      handleSearch(query)
    }
  }

  /**
   * Handle summarization request for a document
   */
  const handleSummarize = async (docId: string) => {
    // Check if already summarized or in progress
    if (summaries[docId] || summarizingIds.has(docId)) {
      return
    }

    setSummarizingIds((prev) => new Set(prev).add(docId))

    try {
      const response = await summarizeDocuments([docId])
      setSummaries((prev) => ({ ...prev, ...response.summaries }))
    } catch (error) {
      console.error('Summarization failed:', error)
      // Show error in UI if needed
    } finally {
      setSummarizingIds((prev) => {
        const next = new Set(prev)
        next.delete(docId)
        return next
      })
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero section with search */}
      <div className="text-center mb-12">
        <h2 className="text-4xl font-bold text-gray-900 mb-4">
          Discover Research & Innovation
        </h2>
        <p className="text-lg text-gray-600 mb-8">
          Search across academic papers and cutting-edge startups using AI-powered hybrid search
        </p>
        
        <SearchBar onSearch={handleSearch} isSearching={isSearching} />
      </div>

      {/* Search error */}
      {searchError && (
        <div className="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900">Search Error</h3>
            <p className="text-sm text-red-700">{searchError}</p>
          </div>
        </div>
      )}

      {/* Results section */}
      {(isSearching || startups.length > 0 || papers.length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar with facets */}
          <aside className="lg:col-span-1">
            <Facets filters={filters} onFilterChange={handleFilterChange} />
          </aside>

          {/* Results list */}
          <div className="lg:col-span-3">
            {isSearching ? (
              <div className="flex items-center justify-center py-20">
                <div className="text-center">
                  <Loader2 className="w-10 h-10 text-primary-600 animate-spin mx-auto mb-4" />
                  <p className="text-gray-600">Searching across startups and research papers...</p>
                </div>
              </div>
            ) : (
              <div className="space-y-8">
                {/* Section 1: Startups from Tavily */}
                {startups.length > 0 && (
                  <div>
                    <div className="mb-4 flex items-center space-x-2">
                      <h2 className="text-2xl font-bold text-gray-900">🏢 Relevant Startups</h2>
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 text-sm font-medium rounded">
                        {startups.length}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-4">
                      Companies and startups working on related problems (via web search)
                    </p>
                    <div className="space-y-4">
                      {startups.map((startup) => (
                        <ResultCard
                          key={startup.id}
                          result={startup}
                          summary={summaries[startup.id]}
                          isSummarizing={summarizingIds.has(startup.id)}
                          onSummarize={() => handleSummarize(startup.id)}
                        />
                      ))}
                    </div>
                  </div>
                )}

                {/* Section 2: Papers from Database */}
                {papers.length > 0 && (
                  <div>
                    <div className="mb-4 flex items-center space-x-2">
                      <h2 className="text-2xl font-bold text-gray-900">📄 Research Papers</h2>
                      <span className="px-2 py-1 bg-green-100 text-green-700 text-sm font-medium rounded">
                        {papers.length}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-4">
                      Academic papers and research addressing this problem
                    </p>
                    <div className="space-y-4">
                      {papers.map((paper) => (
                        <ResultCard
                          key={paper.id}
                          result={paper}
                          summary={summaries[paper.id]}
                          isSummarizing={summarizingIds.has(paper.id)}
                          onSummarize={() => handleSummarize(paper.id)}
                        />
                      ))}
                    </div>
                  </div>
                )}

                {/* No results state */}
                {startups.length === 0 && papers.length === 0 && (
                  <div className="text-center py-20">
                    <p className="text-gray-500">No results found. Try a different query.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isSearching && startups.length === 0 && papers.length === 0 && !query && (
        <div className="text-center py-20">
          <div className="max-w-md mx-auto">
            <p className="text-gray-600 mb-6">
              Try searching for topics like:
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {[
                'solid-state batteries',
                'CRISPR gene therapy',
                'transformer models',
                'carbon capture',
                'quantum computing',
              ].map((example) => (
                <button
                  key={example}
                  onClick={() => handleSearch(example)}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full text-sm transition-colors"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


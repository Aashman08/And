'use client'

import { useState, FormEvent } from 'react'
import { Search, Loader2 } from 'lucide-react'

interface SearchBarProps {
  onSearch: (query: string) => void
  isSearching?: boolean
}

/**
 * SearchBar component for entering search queries.
 * 
 * Features:
 * - Large, prominent search input
 * - Search button with loading state
 * - Enter key support
 * - Auto-focus on mount
 */
export function SearchBar({ onSearch, isSearching = false }: SearchBarProps) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (query.trim() && !isSearching) {
      onSearch(query.trim())
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl mx-auto">
      <div className="relative">
        {/* Search icon */}
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          {isSearching ? (
            <Loader2 className="w-6 h-6 text-gray-400 animate-spin" />
          ) : (
            <Search className="w-6 h-6 text-gray-400" />
          )}
        </div>

        {/* Search input */}
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for papers, startups, or topics..."
          disabled={isSearching}
          autoFocus
          className="w-full pl-12 pr-32 py-4 text-lg border-2 border-gray-300 rounded-xl focus:outline-none focus:border-primary-500 focus:ring-4 focus:ring-primary-100 disabled:bg-gray-50 disabled:text-gray-500 transition-all"
        />

        {/* Search button */}
        <div className="absolute inset-y-0 right-0 pr-2 flex items-center">
          <button
            type="submit"
            disabled={!query.trim() || isSearching}
            className="px-6 py-2 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            Search
          </button>
        </div>
      </div>

      {/* Search tips */}
      <div className="mt-3 text-sm text-gray-500 text-center">
        <p>
          Try: &quot;battery materials&quot; • &quot;gene therapy startups&quot; • &quot;transformer architecture&quot;
        </p>
      </div>
    </form>
  )
}


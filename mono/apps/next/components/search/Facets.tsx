'use client'

import { useState } from 'react'
import { Filter } from 'lucide-react'
import type { SearchFilters, SourceType } from '@/lib/api'

interface FacetsProps {
  filters: SearchFilters
  onFilterChange: (filters: SearchFilters) => void
}

/**
 * Facets component for filtering search results.
 * 
 * Features:
 * - Source type filter (papers/startups)
 * - Year range filter
 * - Clear filters button
 */
export function Facets({ filters, onFilterChange }: FacetsProps) {
  const [localFilters, setLocalFilters] = useState<SearchFilters>(filters)

  const currentYear = new Date().getFullYear()
  const yearOptions = [
    { label: 'Any time', value: undefined },
    { label: 'Last year', value: currentYear - 1 },
    { label: 'Last 3 years', value: currentYear - 3 },
    { label: 'Last 5 years', value: currentYear - 5 },
  ]

  /**
   * Toggle source filter (papers/startups)
   */
  const toggleSource = (source: SourceType) => {
    const currentSources = localFilters.source || []
    const newSources = currentSources.includes(source)
      ? currentSources.filter((s) => s !== source)
      : [...currentSources, source]

    const newFilters = {
      ...localFilters,
      source: newSources.length > 0 ? newSources : undefined,
    }

    setLocalFilters(newFilters)
    onFilterChange(newFilters)
  }

  /**
   * Update year filter
   */
  const updateYearFilter = (year: number | undefined) => {
    const newFilters = {
      ...localFilters,
      year_gte: year,
    }

    setLocalFilters(newFilters)
    onFilterChange(newFilters)
  }

  /**
   * Clear all filters
   */
  const clearFilters = () => {
    const emptyFilters: SearchFilters = {}
    setLocalFilters(emptyFilters)
    onFilterChange(emptyFilters)
  }

  const hasFilters = localFilters.source || localFilters.year_gte

  return (
    <div className="card sticky top-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Filter className="w-5 h-5 text-gray-600" />
          <h3 className="font-semibold text-gray-900">Filters</h3>
        </div>
        {hasFilters && (
          <button
            onClick={clearFilters}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            Clear
          </button>
        )}
      </div>

      {/* Source type filter */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Source Type</h4>
        <div className="space-y-2">
          {(['papers', 'startups'] as SourceType[]).map((source) => {
            const isSelected = localFilters.source?.includes(source) ?? false
            return (
              <label
                key={source}
                className="flex items-center space-x-3 cursor-pointer group"
              >
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => toggleSource(source)}
                  className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700 group-hover:text-gray-900 capitalize">
                  {source}
                </span>
              </label>
            )
          })}
        </div>
      </div>

      {/* Year filter */}
      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-3">Publication Date</h4>
        <div className="space-y-2">
          {yearOptions.map((option) => {
            const isSelected = localFilters.year_gte === option.value
            return (
              <label
                key={option.label}
                className="flex items-center space-x-3 cursor-pointer group"
              >
                <input
                  type="radio"
                  name="year"
                  checked={isSelected}
                  onChange={() => updateYearFilter(option.value)}
                  className="w-4 h-4 text-primary-600 border-gray-300 focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700 group-hover:text-gray-900">
                  {option.label}
                </span>
              </label>
            )
          })}
        </div>
      </div>
    </div>
  )
}


\\\\\\\\\\\\\\\\'use client'

import { useState } from 'react'
import { FileText, Building2, Calendar, Users, Tag, ExternalLink, ChevronDown, ChevronUp, Sparkles, Loader2 } from 'lucide-react'
import type { SearchResult, SummarySection } from '@/lib/api'

interface ResultCardProps {
  result: SearchResult
  summary?: SummarySection
  isSummarizing?: boolean
  onSummarize: () => void
}

/**
 * ResultCard component for displaying search results.
 * 
 * Features:
 * - Paper vs startup styling
 * - Metadata display (authors, venue, year, etc.)
 * - "Why this result" highlights
 * - Expandable AI summary
 * - External links
 */
export function ResultCard({ result, summary, isSummarizing = false, onSummarize }: ResultCardProps) {
  const [showSummary, setShowSummary] = useState(false)

  const isPaper = result.source === 'papers'
  const hasLink = isPaper ? result.metadata.doi : result.metadata.website

  /**
   * Handle summary toggle
   */
  const toggleSummary = () => {
    if (!summary && !isSummarizing) {
      onSummarize()
    }
    setShowSummary(!showSummary)
  }

  return (
    <div className="card hover:shadow-md transition-shadow">
      {/* Header with source badge */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start space-x-3 flex-1">
          {/* Icon */}
          <div className={`mt-1 p-2 rounded-lg ${isPaper ? 'bg-blue-100' : 'bg-green-100'}`}>
            {isPaper ? (
              <FileText className={`w-5 h-5 ${isPaper ? 'text-blue-600' : 'text-green-600'}`} />
            ) : (
              <Building2 className="w-5 h-5 text-green-600" />
            )}
          </div>

          {/* Title and snippet */}
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-1 leading-tight">
              {result.title}
            </h3>
            <p className="text-sm text-gray-600 line-clamp-2 mb-2">
              {result.snippet}
            </p>
          </div>
        </div>

        {/* Score badge */}
        <div className="ml-4 px-3 py-1 bg-gray-100 rounded-full text-sm font-medium text-gray-700">
          {(result.score * 100).toFixed(0)}%
        </div>
      </div>

      {/* Metadata */}
      <div className="flex flex-wrap gap-3 mb-3 text-sm text-gray-600">
        {result.metadata.year && (
          <div className="flex items-center space-x-1">
            <Calendar className="w-4 h-4" />
            <span>{result.metadata.year}</span>
          </div>
        )}

        {isPaper && result.metadata.authors && result.metadata.authors.length > 0 && (
          <div className="flex items-center space-x-1">
            <Users className="w-4 h-4" />
            <span className="truncate max-w-xs">
              {result.metadata.authors.slice(0, 3).join(', ')}
              {result.metadata.authors.length > 3 && ` +${result.metadata.authors.length - 3}`}
            </span>
          </div>
        )}

        {isPaper && result.metadata.venue && (
          <div className="flex items-center space-x-1">
            <Tag className="w-4 h-4" />
            <span className="truncate max-w-xs">{result.metadata.venue}</span>
          </div>
        )}

        {!isPaper && result.metadata.stage && (
          <div className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-medium">
            {result.metadata.stage}
          </div>
        )}
      </div>

      {/* Why this result (highlights) */}
      {result.why_this_result && result.why_this_result.length > 0 && (
        <div className="mb-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h4 className="text-xs font-semibold text-yellow-900 mb-2 uppercase tracking-wide">
            Why this result
          </h4>
          <ul className="space-y-1">
            {result.why_this_result.slice(0, 3).map((highlight, idx) => (
              <li key={idx} className="text-sm text-yellow-900 leading-relaxed">
                • {highlight}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Tags/Concepts */}
      {((isPaper && result.metadata.concepts) || (!isPaper && result.metadata.industry)) && (
        <div className="flex flex-wrap gap-2 mb-3">
          {(isPaper ? result.metadata.concepts : result.metadata.industry)?.slice(0, 5).map((tag) => (
            <span
              key={tag}
              className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-200">
        {/* AI Summary toggle */}
        <button
          onClick={toggleSummary}
          disabled={isSummarizing}
          className="flex items-center space-x-2 text-sm text-primary-600 hover:text-primary-700 font-medium disabled:text-gray-400"
        >
          {isSummarizing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Generating summary...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>{summary ? 'AI Summary' : 'Generate AI Summary'}</span>
              {summary && (showSummary ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />)}
            </>
          )}
        </button>

        {/* External link */}
        {hasLink && (
          <a
            href={isPaper ? `https://doi.org/${result.metadata.doi}` : result.metadata.website}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1 text-sm text-gray-600 hover:text-gray-900"
          >
            <span>{isPaper ? 'View paper' : 'Visit website'}</span>
            <ExternalLink className="w-4 h-4" />
          </a>
        )}
      </div>

      {/* AI Summary (expandable) */}
      {showSummary && summary && (
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
          <h4 className="font-semibold text-gray-900 flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-primary-600" />
            <span>AI-Generated Summary</span>
          </h4>

          <div className="space-y-2 text-sm">
            <div>
              <span className="font-semibold text-gray-700">Problem: </span>
              <span className="text-gray-600">{summary.problem}</span>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Approach: </span>
              <span className="text-gray-600">{summary.approach}</span>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Evidence: </span>
              <span className="text-gray-600">{summary.evidence_or_signals}</span>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Result: </span>
              <span className="text-gray-600">{summary.result}</span>
            </div>
            <div>
              <span className="font-semibold text-gray-700">Limitations: </span>
              <span className="text-gray-600">{summary.limitations}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


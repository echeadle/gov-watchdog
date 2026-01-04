import { useState, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Search, Filter, Download, FileText } from 'lucide-react'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import billService from '../services/billService'
import type { BillSummary } from '../types'

const LEGISLATIVE_SUBJECTS = [
  'All Subjects',
  'Government', // Matches "Government Operations", "Government buildings"
  'Health', // Matches "Health care", "Public health"
  'Immigration', // Matches "Immigration", "Border security"
  'Defense', // Matches "Defense", "Armed Forces"
  'Education', // Matches "Education", "Higher education"
  'Climate', // Matches "Climate change and greenhouse gases"
  'Energy', // Matches "Electric power", "Alternative and renewable resources"
  'Environment', // Matches "Environmental assessment", "Environmental protection"
  'Infrastructure', // Matches "Roads and highways", "Transportation programs"
  'Transportation', // Matches "Aviation", "Railroads", "Maritime"
  'Technology', // Matches "Internet", "Computers and information technology"
  'Agriculture', // Matches agriculture-related bills
  'Commerce', // Matches "Commerce", "Trade"
  'Finance', // Matches "Banking", "Financial services"
  'Labor', // Matches "Employment", "Labor standards"
  'Housing', // Matches "Housing finance", "Public housing"
  'Law', // Matches "Criminal law", "Civil rights"
  'Armed Forces', // Matches "Armed Forces and National Security"
  'Veterans', // Matches "Veterans' benefits", "Veterans' medical care"
  'Foreign Affairs', // Matches "International affairs", "Diplomacy"
  'Taxation', // Matches "Taxation", "Tax"
  'Congressional', // Matches "Congressional operations", "Congressional tributes"
]

const CONGRESS_OPTIONS = [
  { value: '118', label: '118th (2023-2024) - Full Data' },
  { value: '119', label: '119th (Current) - Limited Data' },
  { value: '117', label: '117th (2021-2022)' },
  { value: '116', label: '116th (2019-2020)' },
]

export default function Bills() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [showFilters, setShowFilters] = useState(false)
  const [selectedBills, setSelectedBills] = useState<Set<string>>(new Set())

  // Get params from URL
  const query = searchParams.get('q') || ''
  const party = searchParams.get('party') || ''
  const subject = searchParams.get('subject') || ''
  const congress = searchParams.get('congress') || '118' // Default to 118 (has full subjects/summaries data)
  const page = parseInt(searchParams.get('page') || '1')

  // Local form state
  const [searchInput, setSearchInput] = useState(query)

  // Fetch bills
  const { data, isLoading, error } = useQuery({
    queryKey: ['bills', { q: query, party, subject, congress, page }],
    queryFn: () =>
      billService.searchBills({
        q: query || undefined,
        party: party || undefined,
        subject: subject !== 'All Subjects' ? subject : undefined,
        congress: parseInt(congress),
        page,
        page_size: 20,
      }),
  })

  const updateParam = (key: string, value: string) => {
    const newParams = new URLSearchParams(searchParams)
    if (value) {
      newParams.set(key, value)
    } else {
      newParams.delete(key)
    }
    newParams.set('page', '1') // Reset to page 1 on filter change
    setSearchParams(newParams)
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    updateParam('q', searchInput)
  }

  const handlePageChange = (newPage: number) => {
    const newParams = new URLSearchParams(searchParams)
    newParams.set('page', newPage.toString())
    setSearchParams(newParams)
  }

  // Checkbox handling
  const toggleBill = (billId: string) => {
    const newSelected = new Set(selectedBills)
    if (newSelected.has(billId)) {
      newSelected.delete(billId)
    } else {
      newSelected.add(billId)
    }
    setSelectedBills(newSelected)
  }

  const toggleAllBills = () => {
    if (!data?.results) return
    if (selectedBills.size === data.results.length) {
      setSelectedBills(new Set())
    } else {
      setSelectedBills(new Set(data.results.map(b => b.bill_id)))
    }
  }

  // Export functionality
  const handleExport = () => {
    if (!data?.results) return
    const selectedBillsData = data.results.filter(bill =>
      selectedBills.has(bill.bill_id)
    )
    const exportData = JSON.stringify(selectedBillsData, null, 2)
    const blob = new Blob([exportData], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5) // e.g., 2026-01-04T10-30-15
    link.download = `bills-export-${timestamp}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  // Count active filters
  const activeFiltersCount = [
    query,
    party,
    subject !== 'All Subjects' ? subject : '',
  ].filter(Boolean).length

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <div style={{ backgroundColor: '#fafaf9', minHeight: '100vh' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12">
        {/* Page Header - Editorial Style */}
        <div className="mb-10 pb-6 border-b-2 border-slate-200">
          <div className="flex items-baseline justify-between flex-wrap gap-4">
            <div>
              <h1 className="heading-2 text-slate-900 mb-2">
                Legislative Search
              </h1>
              <p className="text-slate-600 text-lg">
                Explore federal legislation from the U.S. Congress
              </p>
            </div>

            {/* Results count */}
            {data && !isLoading && (
              <div className="font-mono text-sm text-slate-500">
                {data.total} {data.total === 1 ? 'bill' : 'bills'} found
              </div>
            )}
          </div>
        </div>

        {/* Search and Filters Section */}
        <div className="mb-8 space-y-4">
          {/* Search Bar */}
          <form onSubmit={handleSearch} className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                placeholder="Search by title, summary, or subject..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="w-full pl-12 pr-4 py-3.5 text-base border-2 border-slate-200 rounded-lg bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all duration-200 outline-none placeholder:text-slate-400"
              />
            </div>
            <Button
              type="submit"
              className="btn-primary px-6 py-3.5 text-base"
            >
              Search
            </Button>
            <Button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className={`btn-secondary px-6 py-3.5 text-base relative ${
                showFilters ? 'bg-slate-200' : ''
              }`}
            >
              <Filter className="w-5 h-5 mr-2" />
              Filters
              {activeFiltersCount > 0 && (
                <span className="absolute -top-2 -right-2 w-6 h-6 bg-primary-600 text-white text-xs font-bold rounded-full flex items-center justify-center">
                  {activeFiltersCount}
                </span>
              )}
            </Button>
          </form>

          {/* Active Filters Display */}
          {activeFiltersCount > 0 && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-medium text-slate-700">Active filters:</span>
              {query && (
                <span className="badge-primary px-3 py-1">
                  Keyword: {query}
                  <button
                    onClick={() => {
                      updateParam('q', '')
                      setSearchInput('')
                    }}
                    className="ml-2 hover:text-primary-900"
                  >
                    ×
                  </button>
                </span>
              )}
              {party && (
                <span className="badge-primary px-3 py-1">
                  Party: {party === 'D' ? 'Democrat' : party === 'R' ? 'Republican' : 'Independent'}
                  <button
                    onClick={() => updateParam('party', '')}
                    className="ml-2 hover:text-primary-900"
                  >
                    ×
                  </button>
                </span>
              )}
              {subject && subject !== 'All Subjects' && (
                <span className="badge-primary px-3 py-1">
                  Subject: {subject}
                  <button
                    onClick={() => updateParam('subject', '')}
                    className="ml-2 hover:text-primary-900"
                  >
                    ×
                  </button>
                </span>
              )}
              <button
                onClick={() => {
                  setSearchParams(new URLSearchParams({ congress }))
                  setSearchInput('')
                }}
                className="text-sm text-primary-600 hover:text-primary-700 font-medium ml-2"
              >
                Clear all
              </button>
            </div>
          )}

          {/* Filter Panel */}
          {showFilters && (
            <div className="bg-slate-50 border-2 border-slate-200 rounded-lg p-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
                {/* Party Filter */}
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">
                    Sponsor Party
                  </label>
                  <select
                    value={party}
                    onChange={(e) => updateParam('party', e.target.value)}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-lg bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all duration-200 outline-none"
                  >
                    <option value="">All Parties</option>
                    <option value="D">Democrat</option>
                    <option value="R">Republican</option>
                    <option value="I">Independent</option>
                  </select>
                </div>

                {/* Subject Filter */}
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">
                    Subject Area
                  </label>
                  <select
                    value={subject || 'All Subjects'}
                    onChange={(e) => updateParam('subject', e.target.value)}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-lg bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all duration-200 outline-none"
                  >
                    {LEGISLATIVE_SUBJECTS.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Congress Filter */}
                <div>
                  <label className="block text-sm font-semibold text-slate-700 mb-2">
                    Congress Session
                  </label>
                  <select
                    value={congress}
                    onChange={(e) => updateParam('congress', e.target.value)}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-lg bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all duration-200 outline-none"
                  >
                    {CONGRESS_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Selection Controls */}
          {data && data.results.length > 0 && (
            <div className="flex items-center justify-between bg-white border-2 border-slate-200 rounded-lg px-5 py-3">
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedBills.size === data.results.length}
                    onChange={toggleAllBills}
                    className="w-4 h-4 text-primary-600 border-slate-300 rounded focus:ring-2 focus:ring-primary-500"
                  />
                  <span className="text-sm font-medium text-slate-700">
                    Select all on page
                  </span>
                </label>
                <span className="text-sm text-slate-500 font-mono">
                  {selectedBills.size} {selectedBills.size === 1 ? 'bill' : 'bills'} selected
                </span>
              </div>
              <Button
                onClick={handleExport}
                disabled={selectedBills.size === 0}
                className={`btn-primary px-4 py-2 text-sm ${
                  selectedBills.size === 0 ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                <Download className="w-4 h-4 mr-2" />
                Export Selected
              </Button>
            </div>
          )}
        </div>

        {/* Results */}
        {error ? (
          <div className="text-center py-12 px-4 bg-red-50 border-2 border-red-200 rounded-lg">
            <p className="text-red-800 font-semibold mb-2">Error loading bills</p>
            <p className="text-red-600 text-sm">
              The backend API endpoint may not be available yet. Please try again later.
            </p>
          </div>
        ) : isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="bg-white rounded-lg border-2 border-slate-200 p-5 animate-pulse"
              >
                <div className="h-6 bg-slate-200 rounded w-1/4 mb-3"></div>
                <div className="h-4 bg-slate-200 rounded w-full mb-2"></div>
                <div className="h-4 bg-slate-200 rounded w-3/4"></div>
              </div>
            ))}
          </div>
        ) : data && data.results.length > 0 ? (
          <>
            {/* Bills Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
              {data.results.map((bill) => (
                <div
                  key={bill.bill_id}
                  className={`bg-white rounded-lg border-2 p-5 transition-all duration-200 hover:shadow-lg hover:-translate-y-1 ${
                    selectedBills.has(bill.bill_id)
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  {/* Checkbox + Header */}
                  <div className="flex items-start gap-3 mb-3">
                    <input
                      type="checkbox"
                      checked={selectedBills.has(bill.bill_id)}
                      onChange={() => toggleBill(bill.bill_id)}
                      className="mt-1 w-4 h-4 text-primary-600 border-slate-300 rounded focus:ring-2 focus:ring-primary-500 cursor-pointer"
                    />
                    <div className="flex-1">
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <Badge variant="primary" size="md" className="font-mono font-semibold">
                          {bill.type.toUpperCase()} {bill.number}
                        </Badge>
                        <div className="flex items-center gap-1.5 text-xs text-slate-500">
                          <FileText className="w-3.5 h-3.5" />
                          <span className="font-medium">{formatDate(bill.introduced_date)}</span>
                        </div>
                      </div>

                      {/* Bill Title */}
                      <h3 className="font-headline text-base font-semibold text-slate-900 line-clamp-2 mb-2 leading-tight">
                        {bill.title}
                      </h3>

                      {/* Sponsor Info */}
                      {bill.sponsor_name && (
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                          <span className="font-medium">Sponsor:</span>
                          <span>{bill.sponsor_name}</span>
                        </div>
                      )}

                      {/* Latest Action */}
                      {bill.latest_action && (
                        <div className="pt-3 mt-3 border-t border-slate-100">
                          <p className="text-sm text-slate-600 line-clamp-2">
                            <span className="font-semibold text-slate-700">Latest Action: </span>
                            {bill.latest_action}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {data.total_pages > 1 && (
              <div className="flex items-center justify-center gap-2">
                <Button
                  onClick={() => handlePageChange(page - 1)}
                  disabled={page === 1}
                  className="btn-secondary px-4 py-2 disabled:opacity-50"
                >
                  Previous
                </Button>
                <span className="px-4 py-2 text-sm text-slate-600 font-mono">
                  Page {page} of {data.total_pages}
                </span>
                <Button
                  onClick={() => handlePageChange(page + 1)}
                  disabled={page === data.total_pages}
                  className="btn-secondary px-4 py-2 disabled:opacity-50"
                >
                  Next
                </Button>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-12 px-4 bg-slate-50 border-2 border-slate-200 rounded-lg">
            <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-700 font-semibold mb-2">No bills found</p>
            <p className="text-slate-500 text-sm">
              Try adjusting your search terms or filters
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Search, Filter } from 'lucide-react'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import MemberList from '../components/features/MemberList'
import memberService from '../services/memberService'

const STATES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
]

export default function Members() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [showFilters, setShowFilters] = useState(false)

  // Get params from URL
  const query = searchParams.get('q') || ''
  const state = searchParams.get('state') || ''
  const party = searchParams.get('party') || ''
  const chamber = searchParams.get('chamber') || ''
  const page = parseInt(searchParams.get('page') || '1')

  // Local form state
  const [searchInput, setSearchInput] = useState(query)

  // Fetch members
  const { data, isLoading, error } = useQuery({
    queryKey: ['members', { q: query, state, party, chamber, page }],
    queryFn: () =>
      memberService.searchMembers({
        q: query || undefined,
        state: state || undefined,
        party: party || undefined,
        chamber: chamber || undefined,
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

  // Count active filters
  const activeFiltersCount = [state, party, chamber].filter(Boolean).length

  return (
    <div style={{ backgroundColor: '#fafaf9', minHeight: '100vh' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12">
        {/* Page Header - Editorial Style */}
        <div className="mb-10 pb-6 border-b-2 border-slate-200">
        <div className="flex items-baseline justify-between flex-wrap gap-4">
          <div>
            <h1 className="heading-2 text-slate-900 mb-2">
              Congressional Directory
            </h1>
            <p className="text-slate-600 text-lg">
              Complete roster of the {data?.total || 539} members serving in the U.S. Congress
            </p>
          </div>

          {/* Results count */}
          {data && !isLoading && (
            <div className="font-mono text-sm text-slate-500">
              {data.total} {data.total === 1 ? 'member' : 'members'} found
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
              placeholder="Search by name, state, or party..."
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
            {state && (
              <span className="badge-primary px-3 py-1">
                State: {state}
                <button
                  onClick={() => updateParam('state', '')}
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
            {chamber && (
              <span className="badge-primary px-3 py-1">
                {chamber === 'house' ? 'House' : 'Senate'}
                <button
                  onClick={() => updateParam('chamber', '')}
                  className="ml-2 hover:text-primary-900"
                >
                  ×
                </button>
              </span>
            )}
            <button
              onClick={() => {
                setSearchParams(new URLSearchParams())
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
              {/* State Filter */}
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  State
                </label>
                <select
                  value={state}
                  onChange={(e) => updateParam('state', e.target.value)}
                  className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-lg bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all duration-200 outline-none"
                >
                  <option value="">All States</option>
                  {STATES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>

              {/* Party Filter */}
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Party
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

              {/* Chamber Filter */}
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Chamber
                </label>
                <select
                  value={chamber}
                  onChange={(e) => updateParam('chamber', e.target.value)}
                  className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-lg bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all duration-200 outline-none"
                >
                  <option value="">Both Chambers</option>
                  <option value="house">House of Representatives</option>
                  <option value="senate">Senate</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      {error ? (
        <div className="text-center py-12 px-4 bg-red-50 border-2 border-red-200 rounded-lg">
          <p className="text-red-800 font-semibold mb-2">Error loading members</p>
          <p className="text-red-600 text-sm">Please try again or adjust your search criteria.</p>
        </div>
      ) : (
        <MemberList
          members={data?.results || []}
          isLoading={isLoading}
          total={data?.total || 0}
          page={page}
          totalPages={data?.total_pages || 1}
          onPageChange={handlePageChange}
        />
      )}
      </div>
    </div>
  )
}

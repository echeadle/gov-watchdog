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

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Congress Members</h1>

      {/* Search and Filters */}
      <div className="mb-6 space-y-4">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input
              type="text"
              placeholder="Search by name..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button type="submit">Search</Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="w-5 h-5" />
          </Button>
        </form>

        {/* Filters */}
        {showFilters && (
          <div className="flex flex-wrap gap-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                State
              </label>
              <select
                value={state}
                onChange={(e) => updateParam('state', e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="">All States</option>
                {STATES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Party
              </label>
              <select
                value={party}
                onChange={(e) => updateParam('party', e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="">All Parties</option>
                <option value="D">Democrat</option>
                <option value="R">Republican</option>
                <option value="I">Independent</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Chamber
              </label>
              <select
                value={chamber}
                onChange={(e) => updateParam('chamber', e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="">All</option>
                <option value="house">House</option>
                <option value="senate">Senate</option>
              </select>
            </div>

            <div className="flex items-end">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setSearchParams(new URLSearchParams())
                  setSearchInput('')
                }}
              >
                Clear Filters
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      {error ? (
        <div className="text-center py-8 text-red-600">
          Error loading members. Please try again.
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
  )
}

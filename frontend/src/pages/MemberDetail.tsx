import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, ExternalLink, FileText, Vote, FileEdit, MapPin } from 'lucide-react'
import { Card, CardBody } from '../components/ui/Card'
import Badge, { getPartyVariant, getPartyName } from '../components/ui/Badge'
import Button from '../components/ui/Button'
import BillsList from '../components/features/BillsList'
import AmendmentsList from '../components/features/AmendmentsList'
import VoteRecord from '../components/features/VoteRecord'
import memberService from '../services/memberService'

type Tab = 'bills' | 'amendments' | 'votes'

export default function MemberDetail() {
  const { bioguideId } = useParams<{ bioguideId: string }>()
  const [activeTab, setActiveTab] = useState<Tab>('bills')

  const { data: member, isLoading, error } = useQuery({
    queryKey: ['member', bioguideId],
    queryFn: () => memberService.getMember(bioguideId!),
    enabled: !!bioguideId,
  })

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-6 w-32 bg-slate-200 rounded" />
          <div className="h-64 bg-slate-200 rounded-lg" />
          <div className="h-12 bg-slate-200 rounded" />
          <div className="h-96 bg-slate-200 rounded-lg" />
        </div>
      </div>
    )
  }

  if (error || !member) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center py-16 px-4 bg-red-50 border-2 border-red-200 rounded-lg">
          <p className="text-red-800 font-semibold text-xl mb-4">Member not found</p>
          <p className="text-red-600 mb-6">The member you're looking for doesn't exist or may have been removed.</p>
          <Link to="/members" className="btn-primary">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Members
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div style={{ backgroundColor: '#fafaf9', minHeight: '100vh' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-10">
        {/* Back link */}
      <Link
        to="/members"
        className="inline-flex items-center text-slate-600 hover:text-slate-900 mb-8 font-medium transition-colors group"
      >
        <ArrowLeft className="w-4 h-4 mr-2 group-hover:-translate-x-1 transition-transform" />
        Back to Directory
      </Link>

      {/* Member Profile Card - Editorial Style */}
      <div className="bg-white rounded-xl border-2 border-slate-200 shadow-md overflow-hidden mb-8">
        {/* Header with accent bar */}
        <div className={`h-2 ${
          member.party === 'D' ? 'bg-democratic' :
          member.party === 'R' ? 'bg-republican' :
          'bg-independent'
        }`} />

        <div className="p-8">
          <div className="flex flex-col lg:flex-row gap-8">
            {/* Photo */}
            <div className="flex-shrink-0">
              {member.image_url ? (
                <img
                  src={member.image_url}
                  alt={member.name}
                  className="w-48 h-56 object-cover rounded-lg shadow-lg border-2 border-slate-200"
                />
              ) : (
                <div className="w-48 h-56 bg-slate-100 rounded-lg flex items-center justify-center border-2 border-slate-200">
                  <span className="text-6xl text-slate-300">👤</span>
                </div>
              )}
            </div>

            {/* Info */}
            <div className="flex-1">
              {/* Name and Party */}
              <div className="mb-6">
                <div className="flex items-start justify-between flex-wrap gap-4 mb-3">
                  <h1 className="heading-2 text-slate-900">
                    {member.name}
                  </h1>
                  <Badge variant={getPartyVariant(member.party)} size="lg">
                    {getPartyName(member.party)}
                  </Badge>
                </div>
                <p className="text-xl text-slate-600 font-medium">
                  {member.chamber === 'house' ? 'U.S. Representative' : 'U.S. Senator'}
                  {' • '}
                  {member.state}
                  {member.district && ` District ${member.district}`}
                </p>
              </div>

              {/* Details Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pb-6 border-b border-slate-200">
                <div>
                  <div className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1">
                    Chamber
                  </div>
                  <div className="text-lg font-medium text-slate-900 capitalize">
                    {member.chamber === 'house' ? 'House of Representatives' : 'Senate'}
                  </div>
                </div>
                <div>
                  <div className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1">
                    State
                  </div>
                  <div className="text-lg font-medium text-slate-900">
                    {member.state}
                  </div>
                </div>
                {member.district && (
                  <div>
                    <div className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1">
                      District
                    </div>
                    <div className="text-lg font-medium text-slate-900">
                      District {member.district}
                    </div>
                  </div>
                )}
                {member.phone && (
                  <div>
                    <div className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1">
                      Phone
                    </div>
                    <div className="text-lg font-medium text-slate-900 font-mono">
                      {member.phone}
                    </div>
                  </div>
                )}
                {member.address && (
                  <div className="sm:col-span-2">
                    <div className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1 flex items-center gap-1.5">
                      <MapPin className="w-4 h-4" />
                      Washington Office
                    </div>
                    <div className="text-lg font-medium text-slate-900">
                      {member.address}
                    </div>
                  </div>
                )}
              </div>

              {/* Official Website Link */}
              {member.official_url && (
                <div className="mt-6">
                  <a
                    href={member.official_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-5 py-2.5 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 transition-colors shadow-sm hover:shadow-md group"
                  >
                    Official Website
                    <ExternalLink className="w-4 h-4 ml-2 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs - Editorial Style */}
      <div className="flex border-b-2 border-slate-200 mb-8 overflow-x-auto">
        <button
          onClick={() => setActiveTab('bills')}
          className={`flex items-center px-6 py-3 border-b-3 font-semibold transition-all whitespace-nowrap ${
            activeTab === 'bills'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
          }`}
        >
          <FileText className="w-5 h-5 mr-2" />
          Legislation
        </button>
        <button
          onClick={() => setActiveTab('amendments')}
          className={`flex items-center px-6 py-3 border-b-3 font-semibold transition-all whitespace-nowrap ${
            activeTab === 'amendments'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
          }`}
        >
          <FileEdit className="w-5 h-5 mr-2" />
          Amendments
        </button>
        <button
          onClick={() => setActiveTab('votes')}
          className={`flex items-center px-6 py-3 border-b-3 font-semibold transition-all whitespace-nowrap ${
            activeTab === 'votes'
              ? 'border-primary-600 text-primary-600'
              : 'border-transparent text-slate-600 hover:text-slate-900 hover:border-slate-300'
          }`}
        >
          <Vote className="w-5 h-5 mr-2" />
          Voting Record
        </button>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'bills' ? (
          <BillsList bioguideId={bioguideId!} />
        ) : activeTab === 'amendments' ? (
          <AmendmentsList bioguideId={bioguideId!} />
        ) : (
          <VoteRecord bioguideId={bioguideId!} />
        )}
      </div>
      </div>
    </div>
  )
}

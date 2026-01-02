import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, ExternalLink, FileText, Vote } from 'lucide-react'
import { Card, CardBody } from '../components/ui/Card'
import Badge, { getPartyVariant, getPartyName } from '../components/ui/Badge'
import Button from '../components/ui/Button'
import BillsList from '../components/features/BillsList'
import VoteRecord from '../components/features/VoteRecord'
import memberService from '../services/memberService'

type Tab = 'bills' | 'votes'

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
      <div className="animate-pulse">
        <div className="h-8 w-32 bg-gray-200 rounded mb-6" />
        <div className="h-48 bg-gray-200 rounded" />
      </div>
    )
  }

  if (error || !member) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">Member not found</p>
        <Link to="/members" className="text-blue-600 hover:underline">
          Back to Members
        </Link>
      </div>
    )
  }

  return (
    <div>
      {/* Back link */}
      <Link
        to="/members"
        className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft className="w-4 h-4 mr-1" />
        Back to Members
      </Link>

      {/* Member Profile Card */}
      <Card className="mb-6">
        <CardBody>
          <div className="flex flex-col md:flex-row gap-6">
            {/* Photo */}
            <div className="flex-shrink-0">
              {member.image_url ? (
                <img
                  src={member.image_url}
                  alt={member.name}
                  className="w-32 h-40 object-cover rounded-lg shadow"
                />
              ) : (
                <div className="w-32 h-40 bg-gray-200 rounded-lg flex items-center justify-center">
                  <span className="text-4xl text-gray-400">👤</span>
                </div>
              )}
            </div>

            {/* Info */}
            <div className="flex-1">
              <div className="flex items-start justify-between">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">
                    {member.name}
                  </h1>
                  <p className="text-gray-600">
                    {member.chamber === 'house' ? 'Representative' : 'Senator'},{' '}
                    {member.state}
                    {member.district && ` District ${member.district}`}
                  </p>
                </div>
                <Badge variant={getPartyVariant(member.party)} size="md">
                  {getPartyName(member.party)}
                </Badge>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Chamber:</span>{' '}
                  <span className="font-medium capitalize">{member.chamber}</span>
                </div>
                <div>
                  <span className="text-gray-500">State:</span>{' '}
                  <span className="font-medium">{member.state}</span>
                </div>
                {member.district && (
                  <div>
                    <span className="text-gray-500">District:</span>{' '}
                    <span className="font-medium">{member.district}</span>
                  </div>
                )}
                {member.phone && (
                  <div>
                    <span className="text-gray-500">Phone:</span>{' '}
                    <span className="font-medium">{member.phone}</span>
                  </div>
                )}
              </div>

              {member.official_url && (
                <a
                  href={member.official_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-blue-600 hover:underline mt-4"
                >
                  Official Website
                  <ExternalLink className="w-4 h-4 ml-1" />
                </a>
              )}
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        <button
          onClick={() => setActiveTab('bills')}
          className={`flex items-center px-4 py-2 border-b-2 font-medium transition-colors ${
            activeTab === 'bills'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <FileText className="w-4 h-4 mr-2" />
          Bills
        </button>
        <button
          onClick={() => setActiveTab('votes')}
          className={`flex items-center px-4 py-2 border-b-2 font-medium transition-colors ${
            activeTab === 'votes'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          <Vote className="w-4 h-4 mr-2" />
          Votes
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'bills' ? (
        <BillsList bioguideId={bioguideId!} />
      ) : (
        <VoteRecord bioguideId={bioguideId!} />
      )}
    </div>
  )
}

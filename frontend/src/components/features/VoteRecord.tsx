import { useQuery } from '@tanstack/react-query'
import { Card, CardBody } from '../ui/Card'
import Badge from '../ui/Badge'
import memberService from '../../services/memberService'
import type { MemberVote } from '../../types'

interface VoteRecordProps {
  bioguideId: string
}

export default function VoteRecord({ bioguideId }: VoteRecordProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['memberVotes', bioguideId],
    queryFn: () => memberService.getMemberVotes(bioguideId),
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-20 bg-gray-100 rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-600">
        Error loading voting record. Please try again.
      </div>
    )
  }

  const votes: MemberVote[] = data?.results || []

  if (votes.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>No voting records available yet.</p>
        <p className="text-sm mt-2">
          Voting records are populated as votes are synced from Congress.gov.
        </p>
      </div>
    )
  }

  const getVoteBadgeVariant = (vote: string) => {
    switch (vote.toLowerCase()) {
      case 'yea':
      case 'yes':
        return 'success'
      case 'nay':
      case 'no':
        return 'error'
      case 'present':
        return 'warning'
      default:
        return 'default'
    }
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const formatBillId = (billId: string) => {
    // Convert "hr1676-119" to "H.R. 1676"
    // Convert "s1071-119" to "S. 1071"
    // Convert "hjres42-119" to "H.J.Res. 42"
    const match = billId.match(/^([a-z]+)(\d+)-(\d+)$/)
    if (!match) return billId

    const [, type, number] = match
    let formattedType = type.toUpperCase()

    // Format common bill types
    if (type === 'hr') formattedType = 'H.R.'
    else if (type === 's') formattedType = 'S.'
    else if (type === 'hjres') formattedType = 'H.J.Res.'
    else if (type === 'sjres') formattedType = 'S.J.Res.'
    else if (type === 'hconres') formattedType = 'H.Con.Res.'
    else if (type === 'sconres') formattedType = 'S.Con.Res.'
    else if (type === 'hres') formattedType = 'H.Res.'
    else if (type === 'sres') formattedType = 'S.Res.'

    return `${formattedType} ${number}`
  }

  return (
    <div>
      <p className="text-sm text-gray-600 mb-4">
        {data?.total || votes.length} votes on record
      </p>

      <div className="space-y-3">
        {votes.map((vote) => (
          <Card key={vote.vote_id}>
            <CardBody className="py-3">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-baseline gap-2 mb-1">
                    <p className="font-medium text-gray-900">{vote.question}</p>
                    {vote.bill_id && (
                      <span className="text-sm font-semibold text-primary-600">
                        {formatBillId(vote.bill_id)}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500">
                    {formatDate(vote.date)}
                  </p>
                </div>
                <div className="text-right flex-shrink-0">
                  <Badge variant={getVoteBadgeVariant(vote.member_vote)}>
                    {vote.member_vote}
                  </Badge>
                  {vote.result && (
                    <p className="text-xs text-gray-500 mt-1">{vote.result}</p>
                  )}
                </div>
              </div>
            </CardBody>
          </Card>
        ))}
      </div>
    </div>
  )
}

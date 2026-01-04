import { useQuery } from '@tanstack/react-query'
import AmendmentCard from './AmendmentCard'
import amendmentService from '../../services/amendmentService'
import type { AmendmentSummary } from '../../types'

interface AmendmentsListProps {
  bioguideId: string
}

export default function AmendmentsList({ bioguideId }: AmendmentsListProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['memberAmendments', bioguideId],
    queryFn: () => amendmentService.getMemberAmendments(bioguideId, { limit: 50 }),
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-24 bg-gray-100 rounded-lg animate-pulse" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-600">
        Error loading amendments. Please try again.
      </div>
    )
  }

  const amendments = data?.results || []

  return (
    <div>
      {amendments.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No amendments found
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            {data?.total || amendments.length} sponsored amendments
          </p>
          {amendments.map((amendment: AmendmentSummary) => (
            <AmendmentCard key={amendment.amendment_id} amendment={amendment} />
          ))}
        </div>
      )}
    </div>
  )
}

import MemberCard from './MemberCard'
import Button from '../ui/Button'
import type { MemberSummary } from '../../types'

interface MemberListProps {
  members: MemberSummary[]
  isLoading: boolean
  total: number
  page: number
  totalPages: number
  onPageChange: (page: number) => void
}

export default function MemberList({
  members,
  isLoading,
  total,
  page,
  totalPages,
  onPageChange,
}: MemberListProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="h-32 bg-gray-100 rounded-lg animate-pulse"
          />
        ))}
      </div>
    )
  }

  if (members.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No members found</p>
      </div>
    )
  }

  return (
    <div>
      <p className="text-sm text-gray-600 mb-4">
        Showing {members.length} of {total} members
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {members.map((member) => (
          <MemberCard key={member.bioguide_id} member={member} />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-8">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
          >
            Previous
          </Button>

          <span className="text-sm text-gray-600 px-4">
            Page {page} of {totalPages}
          </span>

          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  )
}

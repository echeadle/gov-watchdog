import Badge from '../ui/Badge'
import type { AmendmentSummary } from '../../types'
import { Calendar, FileEdit } from 'lucide-react'

interface AmendmentCardProps {
  amendment: AmendmentSummary
}

export default function AmendmentCard({ amendment }: AmendmentCardProps) {
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  const getChamberBadgeVariant = (chamber: string) => {
    if (chamber === 'house') return 'info' as const
    if (chamber === 'senate') return 'warning' as const
    return 'default' as const
  }

  return (
    <div className="bg-white rounded-lg border-2 border-slate-200 p-5 transition-all duration-200 hover:shadow-lg hover:-translate-y-1 hover:border-slate-300">
      {/* Header: Amendment Number, Chamber & Date */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant="primary" size="md" className="font-mono font-semibold">
            {amendment.type.toUpperCase()} {amendment.amendment_number}
          </Badge>
          <Badge variant={getChamberBadgeVariant(amendment.chamber)} size="sm">
            {amendment.chamber === 'house' ? 'House' : 'Senate'}
          </Badge>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-500 flex-shrink-0">
          <Calendar className="w-3.5 h-3.5" />
          <span className="font-medium">{formatDate(amendment.introduced_date)}</span>
        </div>
      </div>

      {/* Latest Action */}
      {amendment.latest_action && (
        <div className="border-t border-slate-100 pt-3">
          <div className="flex items-start gap-2">
            <FileEdit className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-slate-600 line-clamp-2 mb-1">
                <span className="font-semibold text-slate-700">Latest Action: </span>
                {amendment.latest_action}
              </p>
              {amendment.latest_action_date && (
                <p className="text-xs text-slate-500 font-medium">
                  {formatDate(amendment.latest_action_date)}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

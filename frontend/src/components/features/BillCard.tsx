import Badge from '../ui/Badge'
import type { BillSummary } from '../../types'
import { Calendar } from 'lucide-react'

interface BillCardProps {
  bill: BillSummary
}

export default function BillCard({ bill }: BillCardProps) {
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <div className="bg-white rounded-lg border-2 border-slate-200 p-5 transition-all duration-200 hover:shadow-lg hover:-translate-y-1 hover:border-slate-300">
      {/* Header: Bill Number & Date */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <Badge variant="primary" size="md" className="font-mono font-semibold">
          {bill.type.toUpperCase()} {bill.number}
        </Badge>
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <Calendar className="w-3.5 h-3.5" />
          <span className="font-medium">{formatDate(bill.introduced_date)}</span>
        </div>
      </div>

      {/* Bill Title */}
      <h3 className="font-headline text-lg font-semibold text-slate-900 line-clamp-2 mb-3 leading-tight">
        {bill.title}
      </h3>

      {/* Latest Action */}
      {bill.latest_action && (
        <div className="pt-3 border-t border-slate-100">
          <p className="text-sm text-slate-600 line-clamp-2">
            <span className="font-semibold text-slate-700">Latest Action: </span>
            {bill.latest_action}
          </p>
        </div>
      )}
    </div>
  )
}

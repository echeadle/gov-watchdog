import { Card, CardBody } from '../ui/Card'
import Badge from '../ui/Badge'
import type { BillSummary } from '../../types'

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
    <Card className="hover:shadow-md transition-shadow">
      <CardBody>
        <div className="flex items-start justify-between gap-2 mb-2">
          <Badge variant="default" size="sm">
            {bill.type.toUpperCase()} {bill.number}
          </Badge>
          <span className="text-xs text-gray-500">
            {formatDate(bill.introduced_date)}
          </span>
        </div>

        <h3 className="font-medium text-gray-900 line-clamp-2 mb-2">
          {bill.title}
        </h3>

        {bill.latest_action && (
          <p className="text-sm text-gray-600 line-clamp-2">
            <span className="font-medium">Latest:</span> {bill.latest_action}
          </p>
        )}
      </CardBody>
    </Card>
  )
}

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import BillCard from './BillCard'
import Button from '../ui/Button'
import memberService from '../../services/memberService'

interface BillsListProps {
  bioguideId: string
}

export default function BillsList({ bioguideId }: BillsListProps) {
  const [billType, setBillType] = useState<'sponsored' | 'cosponsored'>('sponsored')

  const { data, isLoading, error } = useQuery({
    queryKey: ['memberBills', bioguideId, billType],
    queryFn: () => memberService.getMemberBills(bioguideId, billType),
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
        Error loading bills. Please try again.
      </div>
    )
  }

  const bills = data?.results || []

  return (
    <div>
      {/* Type toggle */}
      <div className="flex gap-2 mb-4">
        <Button
          variant={billType === 'sponsored' ? 'primary' : 'secondary'}
          size="sm"
          onClick={() => setBillType('sponsored')}
        >
          Sponsored
        </Button>
        <Button
          variant={billType === 'cosponsored' ? 'primary' : 'secondary'}
          size="sm"
          onClick={() => setBillType('cosponsored')}
        >
          Cosponsored
        </Button>
      </div>

      {bills.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No {billType} bills found
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            {data?.total || bills.length} {billType} bills
          </p>
          {bills.map((bill: any) => (
            <BillCard key={bill.bill_id} bill={bill} />
          ))}
        </div>
      )}
    </div>
  )
}

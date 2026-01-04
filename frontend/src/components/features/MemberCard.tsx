import { useNavigate } from 'react-router-dom'
import { Card, CardBody } from '../ui/Card'
import Badge, { getPartyVariant, getPartyName } from '../ui/Badge'
import type { MemberSummary } from '../../types'

interface MemberCardProps {
  member: MemberSummary
}

export default function MemberCard({ member }: MemberCardProps) {
  const navigate = useNavigate()

  const getPartyBorderColor = () => {
    if (member.party === 'D') return 'border-l-democratic'
    if (member.party === 'R') return 'border-l-republican'
    return 'border-l-independent'
  }

  return (
    <div
      onClick={() => navigate(`/members/${member.bioguide_id}`)}
      className={`bg-white rounded-lg border-2 border-slate-200 border-l-4 ${getPartyBorderColor()} p-4 cursor-pointer transition-all duration-200 hover:shadow-lg hover:-translate-y-1 hover:border-slate-300`}
    >
      <div className="flex gap-4">
        {/* Photo */}
        <div className="flex-shrink-0">
          {member.image_url ? (
            <img
              src={member.image_url}
              alt={member.name}
              className="w-20 h-24 object-cover rounded-md border-2 border-slate-200"
            />
          ) : (
            <div className="w-20 h-24 bg-slate-100 rounded-md border-2 border-slate-200 flex items-center justify-center">
              <span className="text-3xl text-slate-300">👤</span>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2">
            <h3 className="font-headline text-lg font-semibold text-slate-900 truncate leading-tight">
              {member.name}
            </h3>
            <Badge variant={getPartyVariant(member.party)} size="md">
              {member.party}
            </Badge>
          </div>

          <p className="text-sm text-slate-600 font-medium mb-1">
            {member.chamber === 'house' ? 'U.S. Representative' : 'U.S. Senator'}
          </p>

          <p className="text-sm text-slate-500">
            {member.state}
            {member.district && ` • District ${member.district}`}
          </p>
        </div>
      </div>
    </div>
  )
}

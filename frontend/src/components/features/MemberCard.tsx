import { useNavigate } from 'react-router-dom'
import { Card, CardBody } from '../ui/Card'
import Badge, { getPartyVariant, getPartyName } from '../ui/Badge'
import type { MemberSummary } from '../../types'

interface MemberCardProps {
  member: MemberSummary
}

export default function MemberCard({ member }: MemberCardProps) {
  const navigate = useNavigate()

  return (
    <Card
      hover
      onClick={() => navigate(`/members/${member.bioguide_id}`)}
      className="transition-all"
    >
      <CardBody>
        <div className="flex gap-4">
          {/* Photo */}
          <div className="flex-shrink-0">
            {member.image_url ? (
              <img
                src={member.image_url}
                alt={member.name}
                className="w-16 h-20 object-cover rounded"
              />
            ) : (
              <div className="w-16 h-20 bg-gray-200 rounded flex items-center justify-center">
                <span className="text-2xl text-gray-400">👤</span>
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <h3 className="font-semibold text-gray-900 truncate">
                {member.name}
              </h3>
              <Badge variant={getPartyVariant(member.party)} size="sm">
                {member.party}
              </Badge>
            </div>

            <p className="text-sm text-gray-600 mt-1">
              {member.chamber === 'house' ? 'Rep.' : 'Sen.'} - {member.state}
              {member.district && `, District ${member.district}`}
            </p>

            <p className="text-xs text-gray-500 mt-2 capitalize">
              {member.chamber}
            </p>
          </div>
        </div>
      </CardBody>
    </Card>
  )
}

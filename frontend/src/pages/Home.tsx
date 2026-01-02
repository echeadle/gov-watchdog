import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'

export default function Home() {
  const [searchQuery, setSearchQuery] = useState('')
  const navigate = useNavigate()

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/members?q=${encodeURIComponent(searchQuery.trim())}`)
    } else {
      navigate('/members')
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
      <h1 className="text-4xl font-bold text-gray-900 mb-4">
        Track Your Representatives
      </h1>
      <p className="text-xl text-gray-600 mb-8 text-center max-w-2xl">
        Search for US Congress members, view their voting records, and stay informed
        about the bills they sponsor.
      </p>

      <form onSubmit={handleSearch} className="w-full max-w-xl">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input
              type="text"
              placeholder="Search by name, state, or party..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button type="submit" variant="primary">
            Search
          </Button>
        </div>
      </form>

      <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-8 w-full max-w-4xl">
        <FeatureCard
          icon="🔍"
          title="Search Members"
          description="Find representatives by name, state, or party affiliation"
        />
        <FeatureCard
          icon="📜"
          title="View Bills"
          description="See what legislation your representatives are sponsoring"
        />
        <FeatureCard
          icon="🗳️"
          title="Track Votes"
          description="Monitor how members vote on important issues"
        />
      </div>
    </div>
  )
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: string
  title: string
  description: string
}) {
  return (
    <div className="text-center p-6 bg-white rounded-lg shadow-sm border border-gray-200">
      <div className="text-4xl mb-3">{icon}</div>
      <h3 className="font-semibold text-lg mb-2">{title}</h3>
      <p className="text-gray-600 text-sm">{description}</p>
    </div>
  )
}

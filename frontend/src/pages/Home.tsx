import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Users, FileText, Vote, TrendingUp, Shield, Bell } from 'lucide-react'
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
    <div>
      {/* Hero Section - Bold Editorial Style */}
      <div className="relative overflow-hidden bg-gradient-editorial">
        {/* Background Pattern */}
        <div className="absolute inset-0 bg-dot-pattern opacity-10" />

        {/* Decorative Elements */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-white/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-accent-500/10 rounded-full blur-3xl" />

        {/* Hero Content */}
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-32">
          {/* Eyebrow */}
          <div className="font-mono text-primary-200 text-sm uppercase tracking-wider mb-6 animate-fade-in">
            Congressional Accountability Platform
          </div>

          {/* Main Headline - BOLD */}
          <h1 className="font-display text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black text-white leading-[0.95] mb-8 max-w-5xl text-balance animate-fade-in-up stagger-1">
            Every Vote.<br />
            Every Bill.<br />
            Every Dollar.
          </h1>

          {/* Subhead */}
          <p className="text-xl md:text-2xl text-primary-100 max-w-3xl mb-12 leading-relaxed animate-fade-in-up stagger-2">
            Track all 539 members of Congress in real-time. Monitor their voting records,
            sponsored legislation, amendments, and legislative activity.
          </p>

          {/* Search Bar - Prominent */}
          <form onSubmit={handleSearch} className="max-w-3xl animate-fade-in-up stagger-3">
            <div className="bg-white rounded-xl shadow-2xl p-3 flex flex-col sm:flex-row gap-3">
              <div className="flex-1 relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search by name, state, or party..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-12 pr-4 py-4 text-lg bg-transparent focus:outline-none text-slate-900 placeholder:text-slate-400"
                />
              </div>
              <Button
                type="submit"
                className="bg-primary-600 text-white px-8 py-4 text-lg font-semibold rounded-lg hover:bg-primary-700 transition-colors shadow-lg hover:shadow-xl"
              >
                Search
              </Button>
            </div>
          </form>

          {/* Stats Bar */}
          <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-8 max-w-4xl animate-fade-in-up stagger-4">
            <StatCard number="539" label="Congress Members" />
            <StatCard number="435" label="House Seats" />
            <StatCard number="100" label="Senate Seats" />
            <StatCard number="Live" label="Real-Time Data" mono={false} />
          </div>
        </div>
      </div>

      {/* Features Section - Clean, Structured */}
      <div style={{ backgroundColor: '#fafaf9' }} className="py-20 md:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Section Header */}
          <div className="text-center mb-16">
            <h2 className="heading-2 text-slate-900 mb-4">
              Complete Congressional Transparency
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Access comprehensive data on legislative activity, voting patterns, and member information.
            </p>
          </div>

        {/* Feature Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          <FeatureCard
            icon={<Search className="w-8 h-8" />}
            title="Advanced Search"
            description="Find any member by name, state, party, or chamber. Filter and sort with precision."
            color="primary"
          />
          <FeatureCard
            icon={<FileText className="w-8 h-8" />}
            title="Bill Tracking"
            description="Monitor sponsored legislation, cosponsored bills, and track their progress through Congress."
            color="accent"
          />
          <FeatureCard
            icon={<Vote className="w-8 h-8" />}
            title="Voting Records"
            description="See how members vote on every issue. Analyze patterns and party alignment."
            color="primary"
          />
          <FeatureCard
            icon={<TrendingUp className="w-8 h-8" />}
            title="Real-Time Updates"
            description="Live data from Congress.gov API. Stay informed as legislation moves forward."
            color="accent"
          />
          <FeatureCard
            icon={<Shield className="w-8 h-8" />}
            title="Amendments"
            description="Track floor amendments proposed by members. See what changes they're advocating."
            color="primary"
          />
          <FeatureCard
            icon={<Bell className="w-8 h-8" />}
            title="AI Assistant"
            description="Ask questions in plain language. Our AI helps you understand congressional activity."
            color="accent"
          />
        </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-slate-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
          <h2 className="font-display text-4xl md:text-5xl font-bold mb-6">
            Democracy Requires Accountability
          </h2>
          <p className="text-xl text-slate-300 mb-10 max-w-2xl mx-auto">
            Start tracking your representatives today. Know how they vote, what they sponsor,
            and who they represent.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              onClick={() => navigate('/members')}
              className="bg-white text-slate-900 px-8 py-4 text-lg font-semibold rounded-lg hover:bg-slate-100 transition-colors shadow-xl"
            >
              <Users className="w-5 h-5 mr-2" />
              Browse All Members
            </Button>
            <Button
              onClick={() => navigate('/chat')}
              className="bg-primary-600 text-white px-8 py-4 text-lg font-semibold rounded-lg hover:bg-primary-700 transition-colors shadow-xl"
            >
              Ask the AI Assistant
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({
  number,
  label,
  mono = true
}: {
  number: string
  label: string
  mono?: boolean
}) {
  return (
    <div className="text-center">
      <div className={`${mono ? 'font-mono' : 'font-display'} text-3xl md:text-4xl font-bold text-white mb-2`}>
        {number}
      </div>
      <div className="text-primary-200 text-sm font-medium tracking-wide">
        {label}
      </div>
    </div>
  )
}

function FeatureCard({
  icon,
  title,
  description,
  color,
}: {
  icon: React.ReactNode
  title: string
  description: string
  color: 'primary' | 'accent'
}) {
  const colorClasses = color === 'primary'
    ? 'text-primary-600 bg-primary-50'
    : 'text-accent-600 bg-accent-50'

  return (
    <div className="group p-8 bg-white rounded-xl border border-slate-200 hover:border-slate-300 hover:shadow-lg transition-all duration-200 hover:-translate-y-1">
      {/* Icon */}
      <div className={`inline-flex p-3 rounded-lg ${colorClasses} mb-5 group-hover:scale-110 transition-transform duration-200`}>
        {icon}
      </div>

      {/* Content */}
      <h3 className="heading-3 text-slate-900 mb-3">
        {title}
      </h3>
      <p className="text-slate-600 leading-relaxed">
        {description}
      </p>
    </div>
  )
}

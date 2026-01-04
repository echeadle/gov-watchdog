// Member types
export interface Member {
  bioguide_id: string
  name: string
  first_name: string
  last_name: string
  party: 'D' | 'R' | 'I' | string
  state: string
  district?: number
  chamber: 'house' | 'senate'
  image_url?: string
  official_url?: string
  phone?: string
  address?: string
  terms?: Term[]
  updated_at?: string
}

export interface MemberSummary {
  bioguide_id: string
  name: string
  party: string
  state: string
  district?: number
  chamber: string
  image_url?: string
}

export interface Term {
  congress: number
  chamber: string
  start_year: number
  end_year?: number
  state: string
  district?: number
  party: string
}

// Bill types
export interface Bill {
  bill_id: string
  congress: number
  type: string
  number: number
  title: string
  short_title?: string
  sponsor_id?: string
  sponsor_name?: string
  sponsor_party?: string
  sponsor_state?: string
  cosponsors_count: number
  introduced_date?: string
  latest_action?: string
  latest_action_date?: string
  policy_area?: string
  subjects?: string[]
}

export interface BillSummary {
  bill_id: string
  type: string
  number: number
  title: string
  sponsor_id?: string
  sponsor_name?: string
  introduced_date?: string
  latest_action?: string
}

// Amendment types
export interface Amendment {
  amendment_id: string
  amendment_number: string
  congress: number
  type: string
  description?: string
  purpose?: string
  chamber: 'house' | 'senate'
  introduced_date?: string
  latest_action?: string
  latest_action_date?: string
  url?: string
}

export interface AmendmentSummary {
  amendment_id: string
  amendment_number: string
  type: string
  chamber: string
  introduced_date?: string
  latest_action?: string
  latest_action_date?: string
}

// Vote types
export interface Vote {
  vote_id: string
  chamber: string
  congress: number
  session: number
  roll_number: number
  date?: string
  question: string
  description?: string
  result?: string
  bill_id?: string
  totals: VoteTotals
  member_votes: Record<string, string>
}

export interface VoteTotals {
  yea: number
  nay: number
  present: number
  not_voting: number
}

export interface MemberVote {
  vote_id: string
  date?: string
  question: string
  bill_id?: string
  member_vote: string
  result?: string
}

// API Response types
export interface PaginatedResponse<T> {
  results: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface MemberStats {
  total: number
  by_party: Record<string, number>
  by_chamber: Record<string, number>
}

// Search params
export interface MemberSearchParams {
  q?: string
  state?: string
  party?: string
  chamber?: string
  page?: number
  page_size?: number
}

// Chat types
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export interface ChatRequest {
  message: string
  conversation_id?: string
}

export interface ChatResponse {
  response: string
  conversation_id: string
}

import api from './api'
import type { Member, MemberSummary, MemberSearchParams, PaginatedResponse, MemberStats } from '../types'

export const memberService = {
  // Search/list members
  async searchMembers(params: MemberSearchParams): Promise<PaginatedResponse<MemberSummary>> {
    const { data } = await api.get('/members/', { params })
    return data
  },

  // Get single member by bioguide ID
  async getMember(bioguideId: string): Promise<Member> {
    const { data } = await api.get(`/members/${bioguideId}/`)
    return data
  },

  // Get member statistics
  async getStats(): Promise<MemberStats> {
    const { data } = await api.get('/members/stats/')
    return data
  },

  // Get states with member counts
  async getStates(): Promise<{ states: { state: string; count: number }[] }> {
    const { data } = await api.get('/members/states/')
    return data
  },

  // Get member's bills
  async getMemberBills(
    bioguideId: string,
    type: 'sponsored' | 'cosponsored' = 'sponsored',
    limit = 20,
    offset = 0
  ) {
    const { data } = await api.get(`/members/${bioguideId}/bills/`, {
      params: { type, limit, offset },
    })
    return data
  },

  // Get member's voting record
  async getMemberVotes(bioguideId: string, limit = 20, offset = 0) {
    const { data } = await api.get(`/members/${bioguideId}/votes/`, {
      params: { limit, offset },
    })
    return data
  },
}

export default memberService

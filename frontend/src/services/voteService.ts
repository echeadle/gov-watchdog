import api from './api'
import type { Vote, VoteSummary } from '../types'

export const voteService = {
  // Get vote by ID
  async getVote(voteId: string): Promise<Vote> {
    const { data } = await api.get(`/votes/${voteId}/`)
    return data
  },

  // Get recent votes
  async getRecentVotes(params: {
    chamber?: string
    congress?: number
    session?: number
    limit?: number
    offset?: number
  }) {
    const { data } = await api.get('/votes/', { params })
    return data
  },
}

export default voteService

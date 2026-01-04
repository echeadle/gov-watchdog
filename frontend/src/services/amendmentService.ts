import api from './api'
import type { Amendment, AmendmentSummary } from '../types'

export const amendmentService = {
  // Get amendments for a member
  async getMemberAmendments(
    bioguideId: string,
    params?: {
      limit?: number
      offset?: number
    }
  ): Promise<{ results: AmendmentSummary[]; total: number }> {
    const { data } = await api.get(`/members/${bioguideId}/amendments/`, {
      params,
    })
    return data
  },

  // Get amendment by ID (if we add this endpoint later)
  async getAmendment(amendmentId: string): Promise<Amendment> {
    const { data } = await api.get(`/amendments/${amendmentId}/`)
    return data
  },
}

export default amendmentService

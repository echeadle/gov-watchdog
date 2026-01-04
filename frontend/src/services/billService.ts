import api from './api'
import type { Bill, BillSummary } from '../types'

export const billService = {
  // Get bill by ID
  async getBill(billId: string): Promise<Bill> {
    const { data } = await api.get(`/bills/${billId}/`)
    return data
  },

  // Get bill actions
  async getBillActions(billId: string, limit = 20) {
    const { data } = await api.get(`/bills/${billId}/actions/`, {
      params: { limit },
    })
    return data
  },

  // Search bills
  async searchBills(params: {
    q?: string
    congress?: number
    type?: string
    sponsor_id?: string
    party?: string
    subject?: string
    page?: number
    page_size?: number
  }) {
    try {
      const { data } = await api.get('/bills/search/', { params })
      return data
    } catch (error: any) {
      // If the endpoint doesn't exist yet, return mock data for development
      if (error.response?.status === 404) {
        console.warn('Bills search endpoint not yet implemented. Using mock data.')
        return {
          results: [],
          total: 0,
          page: params.page || 1,
          page_size: params.page_size || 20,
          total_pages: 0,
        }
      }
      throw error
    }
  },
}

export default billService

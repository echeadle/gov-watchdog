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
    congress?: number
    type?: string
    sponsor_id?: string
    page?: number
    page_size?: number
  }) {
    const { data } = await api.get('/bills/', { params })
    return data
  },
}

export default billService

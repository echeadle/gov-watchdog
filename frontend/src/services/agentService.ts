import api from './api'
import type { ChatRequest, ChatResponse } from '../types'

export const agentService = {
  // Send a chat message
  async chat(message: string, conversationId?: string): Promise<ChatResponse> {
    const { data } = await api.post('/agent/chat/', {
      message,
      conversation_id: conversationId,
    })
    return data
  },

  // Get conversation history
  async getConversation(conversationId: string) {
    const { data } = await api.get(`/agent/conversations/${conversationId}/`)
    return data
  },

  // Clear conversation
  async clearConversation(conversationId: string) {
    await api.delete(`/agent/conversations/${conversationId}/`)
  },
}

export default agentService

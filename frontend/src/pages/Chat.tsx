import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Trash2 } from 'lucide-react'
import { Card } from '../components/ui/Card'
import Button from '../components/ui/Button'
import agentService from '../services/agentService'
import type { ChatMessage } from '../types'

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content:
        "Hello! I'm your Gov Watchdog assistant. I can help you find information about Congress members, their voting records, and sponsored legislation. What would you like to know?",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | undefined>()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleClear = async () => {
    if (conversationId) {
      try {
        await agentService.clearConversation(conversationId)
      } catch (e) {
        // Ignore errors on clear
      }
    }
    setMessages([
      {
        id: '1',
        role: 'assistant',
        content:
          "Hello! I'm your Gov Watchdog assistant. I can help you find information about Congress members, their voting records, and sponsored legislation. What would you like to know?",
        timestamp: new Date(),
      },
    ])
    setConversationId(undefined)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await agentService.chat(input.trim(), conversationId)

      if (response.conversation_id) {
        setConversationId(response.conversation_id)
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div style={{ backgroundColor: '#fafaf9', minHeight: '100vh' }}>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12">
        {/* Page Header */}
        <div className="mb-10 pb-6 border-b-2 border-slate-200">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="heading-2 text-slate-900 mb-2">
              AI Research Assistant
            </h1>
            <p className="text-slate-600 text-lg max-w-2xl">
              Ask questions about Congress members, their voting records, sponsored legislation,
              and legislative activity. Powered by Claude AI.
            </p>
          </div>
          <Button
            variant="secondary"
            onClick={handleClear}
            className="flex items-center gap-2"
          >
            <Trash2 className="w-4 h-4" />
            New Conversation
          </Button>
        </div>
      </div>

      {/* Chat Interface */}
      <div className="bg-white rounded-xl border-2 border-slate-200 shadow-lg overflow-hidden h-[600px] flex flex-col">
        {/* Messages Area */}
        <div style={{ backgroundColor: '#fafaf9' }} className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-4 ${
                message.role === 'user' ? 'flex-row-reverse' : ''
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm ${
                  message.role === 'user'
                    ? 'bg-primary-600 text-white'
                    : 'bg-white border-2 border-slate-200 text-slate-700'
                }`}
              >
                {message.role === 'user' ? (
                  <User className="w-5 h-5" />
                ) : (
                  <Bot className="w-6 h-6" />
                )}
              </div>

              {/* Message Bubble */}
              <div
                className={`flex-1 max-w-[85%] ${
                  message.role === 'user' ? 'flex justify-end' : ''
                }`}
              >
                <div
                  className={`rounded-xl px-5 py-3.5 shadow-sm ${
                    message.role === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'text-slate-900'
                  }`}
                  style={message.role === 'assistant' ? {
                    backgroundColor: '#f8f8ff',
                    border: '1px solid rgba(79, 70, 229, 0.08)'
                  } : undefined}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">
                    {message.content}
                  </p>
                  <div
                    className={`text-xs mt-2 ${
                      message.role === 'user' ? 'text-primary-100' : 'text-slate-400'
                    }`}
                  >
                    {message.timestamp.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                </div>
              </div>
            </div>
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex gap-4">
              <div className="w-10 h-10 rounded-lg bg-white border-2 border-slate-200 flex items-center justify-center shadow-sm">
                <Bot className="w-6 h-6 text-slate-700" />
              </div>
              <div style={{ backgroundColor: '#f8f8ff', border: '1px solid rgba(79, 70, 229, 0.08)' }} className="rounded-xl px-5 py-3.5 shadow-sm">
                <div className="flex space-x-1.5">
                  <div className="w-2.5 h-2.5 bg-primary-400 rounded-full animate-bounce" />
                  <div
                    className="w-2.5 h-2.5 bg-primary-400 rounded-full animate-bounce"
                    style={{ animationDelay: '0.1s' }}
                  />
                  <div
                    className="w-2.5 h-2.5 bg-primary-400 rounded-full animate-bounce"
                    style={{ animationDelay: '0.2s' }}
                  />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <form
          onSubmit={handleSubmit}
          className="border-t-2 border-slate-200 p-4 bg-white flex gap-3"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about Congress members, bills, votes, or amendments..."
            className="flex-1 px-5 py-3.5 border-2 border-slate-200 rounded-lg bg-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all duration-200 outline-none placeholder:text-slate-400 text-base"
            disabled={isLoading}
          />
          <Button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="btn-primary px-6 py-3.5 shadow-md hover:shadow-lg transition-all"
          >
            <Send className="w-5 h-5" />
          </Button>
        </form>
      </div>

      {/* Helper Text */}
      <div className="mt-6 text-center">
        <p className="text-sm text-slate-500">
          <span className="font-semibold">Example queries:</span> "Find all California representatives" • "Show me bills by Rep. Smith" • "What are the latest votes?"
        </p>
      </div>
      </div>
    </div>
  )
}

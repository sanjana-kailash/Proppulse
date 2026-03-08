import { useEffect, useRef, useState } from 'react'
import axios from 'axios'

const API = ''

const STARTER_PROMPTS = [
  "Is it a good time to sell?",
  "What's the outlook for buyers?",
  "What's driving prices?",
]

export default function ChatAssistant({ suburb }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Ask about ${suburb} and I'll answer from the local market data.`,
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const threadRef = useRef(null)

  useEffect(() => {
    setMessages([
      {
        role: 'assistant',
        content: `Ask about ${suburb} and I'll answer from the local market data.`,
      },
    ])
    setInput('')
    setIsLoading(false)
  }, [suburb])

  useEffect(() => {
    threadRef.current?.scrollTo({
      top: threadRef.current.scrollHeight,
      behavior: 'smooth',
    })
  }, [messages, isLoading])

  async function sendQuestion(question) {
    const trimmed = question.trim()
    if (!trimmed || isLoading) return

    setMessages((current) => [...current, { role: 'user', content: trimmed }])
    setInput('')
    setIsLoading(true)

    try {
      const res = await axios.post(`${API}/api/chat`, {
        suburb,
        question: trimmed,
      })

      setMessages((current) => [
        ...current,
        { role: 'assistant', content: res.data.answer },
      ])
    } catch (err) {
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          content: err.response?.data?.detail ?? 'Chat is unavailable right now.',
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    sendQuestion(input)
  }

  return (
    <section className="rounded-2xl border border-gray-200 bg-white shadow-sm">
      <div className="border-b border-gray-100 px-5 py-4">
        <h2 className="text-lg font-semibold text-gray-900">Suburb Assistant</h2>
        <p className="mt-1 text-sm text-gray-500">Questions stay grounded in the saved suburb context.</p>
      </div>

      <div className="px-5 pt-4">
        <div className="flex flex-wrap gap-2">
          {STARTER_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => sendQuestion(prompt)}
              className="rounded-full border border-blue-100 bg-blue-50 px-3 py-1.5 text-xs font-medium text-blue-700 transition hover:border-blue-200 hover:bg-blue-100"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      <div ref={threadRef} className="mt-4 max-h-[360px] space-y-3 overflow-y-auto px-5 pb-4">
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
              message.role === 'assistant'
                ? 'bg-slate-900 text-white'
                : 'ml-auto bg-gray-100 text-gray-800'
            }`}
          >
            {message.content}
          </div>
        ))}

        {isLoading && (
          <div className="max-w-[90%] rounded-2xl bg-slate-900 px-4 py-3 text-sm text-white">
            Thinking...
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="border-t border-gray-100 p-4">
        <div className="flex gap-3">
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={`Ask about ${suburb}...`}
            className="flex-1 rounded-xl border border-gray-200 px-4 py-3 text-sm outline-none transition focus:border-blue-400"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
          >
            Send
          </button>
        </div>
      </form>
    </section>
  )
}

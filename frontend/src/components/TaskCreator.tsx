import { useState } from 'react'
import { Send, Sparkles, Wand2, Code2, ChevronDown, ChevronUp } from 'lucide-react'
import axios from 'axios'

export function TaskCreator() {
  const [description, setDescription] = useState('')
  const [context, setContext] = useState('')
  const [loading, setLoading] = useState(false)
  const [showContext, setShowContext] = useState(false)
  const [focused, setFocused] = useState(false)

  const handleSubmit = async () => {
    if (!description.trim()) return
    setLoading(true)
    try {
      await axios.post('/api/tasks', { description, context, max_iterations: 3, parallel_candidates: 2 })
      setDescription('')
      setContext('')
    } catch (error) {
      console.error('Failed:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative overflow-hidden rounded-2xl" style={{ border: '1px solid rgba(255,255,255,0.07)', backgroundColor: '#0c0c1e' }}>
      {/* Top accent */}
      <div className="absolute top-0 left-0 right-0 h-[1px]" style={{ background: 'linear-gradient(90deg, transparent, rgba(34,211,238,0.6), transparent)' }} />
      {/* Ambient blobs */}
      <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full blur-3xl" style={{ backgroundColor: 'rgba(34,211,238,0.05)' }} />
      <div className="pointer-events-none absolute -left-16 -bottom-16 h-48 w-48 rounded-full blur-3xl" style={{ backgroundColor: 'rgba(167,139,250,0.05)' }} />

      <div className="relative p-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl" style={{ background: 'linear-gradient(135deg, #0891b2, #7c3aed)', boxShadow: '0 4px 20px rgba(34,211,238,0.2)' }}>
            <Wand2 className="h-5 w-5 text-white" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white">New Task</h2>
            <p className="text-xs" style={{ color: 'rgba(255,255,255,0.35)' }}>Describe what you want to build</p>
          </div>
        </div>

        <div className="space-y-3">
          {/* Description textarea */}
          <div
            className="relative rounded-xl transition-all duration-200"
            style={{
              border: focused ? '1px solid rgba(34,211,238,0.4)' : '1px solid rgba(255,255,255,0.07)',
              backgroundColor: 'rgba(255,255,255,0.03)',
              boxShadow: focused ? '0 0 0 3px rgba(34,211,238,0.08)' : undefined,
            }}
          >
            <div className="flex items-center gap-2 px-4 pt-3 pb-1">
              <Code2 className="h-3.5 w-3.5 shrink-0" style={{ color: 'rgba(34,211,238,0.7)' }} />
              <span className="text-[10px] font-semibold uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Task</span>
            </div>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              placeholder="e.g., Write a Python function to calculate Fibonacci numbers using memoization..."
              rows={4}
              className="w-full bg-transparent px-4 pb-3 text-sm text-white focus:outline-none resize-none"
              style={{ caretColor: '#22d3ee' }}
            />
          </div>

          {/* Context toggle */}
          <button
            type="button"
            onClick={() => setShowContext(v => !v)}
            className="flex items-center gap-1.5 text-xs transition-colors"
            style={{ color: 'rgba(255,255,255,0.35)' }}
            onMouseEnter={e => (e.currentTarget.style.color = 'rgba(255,255,255,0.6)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'rgba(255,255,255,0.35)')}
          >
            <Sparkles className="h-3 w-3" style={{ color: 'rgba(167,139,250,0.6)' }} />
            Add context
            {showContext ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          </button>

          {showContext && (
            <div className="rounded-xl px-4 py-3 animate-slide-up" style={{ border: '1px solid rgba(255,255,255,0.07)', backgroundColor: 'rgba(255,255,255,0.03)' }}>
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="h-3.5 w-3.5" style={{ color: 'rgba(167,139,250,0.7)' }} />
                <span className="text-[10px] font-semibold uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Context</span>
              </div>
              <input
                type="text"
                value={context}
                onChange={e => setContext(e.target.value)}
                placeholder="Additional requirements, constraints, or examples..."
                className="w-full bg-transparent text-sm text-white focus:outline-none"
                style={{ caretColor: '#a78bfa' }}
              />
            </div>
          )}

          {/* Submit button */}
          <button
            onClick={handleSubmit}
            disabled={loading || !description.trim()}
            className="group relative w-full overflow-hidden rounded-xl py-3 text-sm font-semibold text-white transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <div className="absolute inset-0 btn-gradient" />
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity" style={{ backgroundColor: 'rgba(255,255,255,0.1)' }} />
            <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700" style={{ background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent)' }} />
            <span className="relative flex items-center justify-center gap-2">
              {loading ? (
                <>
                  <div className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                  Forging…
                </>
              ) : (
                <>
                  <Send className="h-4 w-4" />
                  Forge Code
                </>
              )}
            </span>
          </button>
        </div>
      </div>
    </div>
  )
}

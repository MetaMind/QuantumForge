import { useState } from 'react'
import { Send, Sparkles, Wand2, Code2 } from 'lucide-react'
import axios from 'axios'

export function TaskCreator() {
  const [description, setDescription] = useState('')
  const [context, setContext] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    if (!description.trim()) return
    setLoading(true)
    try {
      await axios.post('/api/tasks', {
        description,
        context,
        max_iterations: 3,
        parallel_candidates: 2
      })
      setDescription('')
      setContext('')
    } catch (error) {
      console.error('Failed:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-slate-900 to-slate-950 p-6">
      <div className="absolute inset-0 bg-grid opacity-20" />
      <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-blue-500/10 blur-3xl" />
      <div className="absolute -left-20 -bottom-20 h-64 w-64 rounded-full bg-purple-500/10 blur-3xl" />
      
      <div className="relative">
        <div className="flex items-center gap-3 mb-6">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg shadow-blue-500/25">
            <Wand2 className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">New Engineering Task</h2>
            <p className="text-sm text-slate-400">Describe what you want to build</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="group">
            <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
              <Code2 className="h-4 w-4 text-blue-400" />
              Task Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., Write a Python function to calculate Fibonacci numbers using memoization..."
              className="w-full min-h-[120px] rounded-xl border border-white/10 bg-slate-950/50 px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:border-blue-500/50 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all resize-none"
            />
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
              <Sparkles className="h-4 w-4 text-purple-400" />
              Context (Optional)
            </label>
            <input
              type="text"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Additional requirements, constraints, or examples..."
              className="w-full rounded-xl border border-white/10 bg-slate-950/50 px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:border-purple-500/50 focus:outline-none focus:ring-2 focus:ring-purple-500/20 transition-all"
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={loading || !description.trim()}
            className="group relative w-full overflow-hidden rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 p-px disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <div className="relative flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-3 transition-all group-hover:bg-opacity-0">
              {loading ? (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              ) : (
                <Send className="h-5 w-5 text-white" />
              )}
              <span className="font-semibold text-white">
                {loading ? 'Forging Code...' : 'Forge Code'}
              </span>
            </div>
            <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent transition-transform group-hover:translate-x-full duration-1000" />
          </button>
        </div>
      </div>
    </div>
  )
}

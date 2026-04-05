import React, { useEffect } from 'react'
import { useQuery } from 'react-query'
import { formatDistanceToNow } from 'date-fns'
import { CheckCircle2, XCircle, Loader2, Clock, ChevronRight, Terminal, Sparkles } from 'lucide-react'
import { useStore } from '../store/useStore'
import axios from 'axios'

type StatusConfig = {
  icon: React.ElementType
  color: string
  borderColor: string
  bgColor: string
  dotColor: string
  label: string
  animate?: boolean
}

const statusConfig: Record<string, StatusConfig> = {
  pending:    { icon: Clock,        color: '#fbbf24', borderColor: 'rgba(251,191,36,0.2)',  bgColor: 'rgba(251,191,36,0.08)',  dotColor: '#fbbf24', label: 'Pending'    },
  planning:   { icon: Sparkles,     color: '#a78bfa', borderColor: 'rgba(167,139,250,0.2)', bgColor: 'rgba(167,139,250,0.08)', dotColor: '#a78bfa', label: 'Planning'   },
  executing:  { icon: Loader2,      color: '#22d3ee', borderColor: 'rgba(34,211,238,0.2)',  bgColor: 'rgba(34,211,238,0.08)',  dotColor: '#22d3ee', label: 'Executing',  animate: true },
  evaluating: { icon: Loader2,      color: '#818cf8', borderColor: 'rgba(129,140,248,0.2)', bgColor: 'rgba(129,140,248,0.08)', dotColor: '#818cf8', label: 'Evaluating', animate: true },
  fixing:     { icon: Terminal,     color: '#fb923c', borderColor: 'rgba(251,146,60,0.2)',  bgColor: 'rgba(251,146,60,0.08)',  dotColor: '#fb923c', label: 'Fixing'     },
  completed:  { icon: CheckCircle2, color: '#34d399', borderColor: 'rgba(52,211,153,0.2)',  bgColor: 'rgba(52,211,153,0.08)',  dotColor: '#34d399', label: 'Completed'  },
  failed:     { icon: XCircle,      color: '#fb7185', borderColor: 'rgba(251,113,133,0.2)', bgColor: 'rgba(251,113,133,0.08)', dotColor: '#fb7185', label: 'Failed'     },
}

export function TaskList() {
  const { tasks, addTask, setSelectedTask, selectedTask } = useStore()

  const { data: fetchedData } = useQuery(
    'tasks',
    async () => {
      const res = await axios.get('/api/tasks')
      return res.data
    },
    { refetchOnWindowFocus: false }
  )

  // Load tasks from HTTP response into the store on mount
  useEffect(() => {
    if (!fetchedData?.tasks) return
    const currentIds = new Set(useStore.getState().tasks.map((t: any) => t.task_id))
    fetchedData.tasks.forEach((task: any) => {
      if (!currentIds.has(task.task_id)) {
        addTask(task)
      }
    })
  }, [fetchedData, addTask])

  return (
    <div className="flex flex-col overflow-hidden rounded-2xl" style={{ border: '1px solid rgba(255,255,255,0.07)', backgroundColor: '#0c0c1e' }}>
      <div className="h-[1px] w-full" style={{ background: 'linear-gradient(90deg, transparent, rgba(167,139,250,0.5), transparent)' }} />

      <div className="flex items-center gap-3 px-5 py-4" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
        <Terminal className="h-4 w-4" style={{ color: '#a78bfa' }} />
        <h3 className="text-sm font-bold" style={{ color: 'rgba(255,255,255,0.8)' }}>Active Tasks</h3>
        <span className="ml-auto flex h-5 min-w-[20px] items-center justify-center rounded-full px-1.5 text-[10px] font-bold" style={{ backgroundColor: 'rgba(167,139,250,0.2)', color: '#c4b5fd' }}>
          {tasks.length}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto" style={{ maxHeight: '460px' }}>
        {tasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl" style={{ border: '1px solid rgba(255,255,255,0.06)', backgroundColor: 'rgba(255,255,255,0.03)' }}>
              <Clock className="h-6 w-6" style={{ color: 'rgba(255,255,255,0.2)' }} />
            </div>
            <p className="text-sm" style={{ color: 'rgba(255,255,255,0.25)' }}>No tasks yet</p>
            <p className="text-xs mt-1" style={{ color: 'rgba(255,255,255,0.15)' }}>Create one to get started</p>
          </div>
        ) : (
          <div>
            {tasks.map((task: any) => {
              const cfg = statusConfig[task.status] ?? statusConfig.pending
              const Icon = cfg.icon
              const isSelected = selectedTask?.task_id === task.task_id

              return (
                <div
                  key={task.task_id}
                  onClick={() => setSelectedTask(task)}
                  className="group relative cursor-pointer px-5 py-4"
                  style={{
                    borderBottom: '1px solid rgba(255,255,255,0.04)',
                    backgroundColor: isSelected ? 'rgba(255,255,255,0.04)' : undefined,
                    transition: 'background-color 0.15s',
                  }}
                  onMouseEnter={e => { if (!isSelected) (e.currentTarget as HTMLElement).style.backgroundColor = 'rgba(255,255,255,0.025)' }}
                  onMouseLeave={e => { if (!isSelected) (e.currentTarget as HTMLElement).style.backgroundColor = '' }}
                >
                  {isSelected && (
                    <div className="absolute left-0 top-3 bottom-3 w-[2px] rounded-r-full" style={{ background: 'linear-gradient(180deg, #22d3ee, #a78bfa)' }} />
                  )}

                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg" style={{ border: `1px solid ${cfg.borderColor}`, backgroundColor: cfg.bgColor }}>
                      <Icon className={`h-4 w-4 ${cfg.animate ? 'animate-spin' : ''}`} style={{ color: cfg.color }} />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className="truncate text-sm font-medium" style={{ color: 'rgba(255,255,255,0.75)' }}>
                          {task.description}
                        </p>
                        <ChevronRight className="h-3.5 w-3.5 shrink-0" style={{ color: isSelected ? '#22d3ee' : 'rgba(255,255,255,0.2)', transform: isSelected ? 'rotate(90deg)' : undefined, transition: 'all 0.2s' }} />
                      </div>

                      <div className="mt-1.5 flex items-center gap-2 flex-wrap">
                        <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider" style={{ backgroundColor: cfg.bgColor, color: cfg.color, border: `1px solid ${cfg.borderColor}` }}>
                          <span className="h-1 w-1 rounded-full" style={{ backgroundColor: cfg.dotColor }} />
                          {cfg.label}
                        </span>
                        <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.25)' }}>
                          {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
                        </span>
                        {task.metrics?.success_rate !== undefined && (
                          <span className="text-[10px] font-semibold" style={{ color: task.metrics.success_rate > 0.8 ? '#34d399' : '#fbbf24' }}>
                            {(task.metrics.success_rate * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

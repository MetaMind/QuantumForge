import { useEffect } from 'react'
import { useQuery } from 'react-query'
import { formatDistanceToNow } from 'date-fns'
import { 
  CheckCircle2, 
  XCircle, 
  Loader2, 
  Clock, 
  ChevronRight,
  Terminal,
  Sparkles
} from 'lucide-react'
import { useStore } from '../store/useStore'
import axios from 'axios'

const statusConfig = {
  pending: { icon: Clock, color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', label: 'Pending' },
  planning: { icon: Sparkles, color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20', label: 'Planning' },
  executing: { icon: Loader2, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20', label: 'Executing', animate: true },
  evaluating: { icon: Loader2, color: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/20', label: 'Evaluating', animate: true },
  fixing: { icon: Terminal, color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20', label: 'Fixing' },
  completed: { icon: CheckCircle2, color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20', label: 'Completed' },
  failed: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20', label: 'Failed' },
}

export function TaskList() {
  const { tasks, setSelectedTask, selectedTask } = useStore()

  const { data: initialTasks } = useQuery('tasks', async () => {
    const response = await axios.get('/api/tasks')
    return response.data
  })

  useEffect(() => {
    if (initialTasks?.tasks) {
      initialTasks.tasks.forEach((task: any) => {
        if (!tasks.find(t => t.task_id === task.task_id)) {
          // Add to store
        }
      })
    }
  }, [initialTasks])

  return (
    <div className="rounded-2xl border border-white/10 bg-slate-950/50 overflow-hidden">
      <div className="flex items-center justify-between border-b border-white/10 px-6 py-4">
        <div className="flex items-center gap-3">
          <Terminal className="h-5 w-5 text-blue-400" />
          <h3 className="font-bold text-white">Active Tasks</h3>
          <span className="rounded-full bg-slate-800 px-3 py-1 text-xs font-semibold text-slate-400">
            {tasks.length}
          </span>
        </div>
      </div>

      <div className="max-h-[500px] overflow-y-auto">
        {tasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="mb-4 rounded-full bg-slate-800/50 p-4">
              <Clock className="h-8 w-8 text-slate-600" />
            </div>
            <p className="text-slate-500">No tasks yet. Create one to get started.</p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {tasks.map((task) => {
              const config = statusConfig[task.status as keyof typeof statusConfig] || statusConfig.pending
              const Icon = config.icon
              const isSelected = selectedTask?.task_id === task.task_id

              return (
                <div
                  key={task.task_id}
                  onClick={() => setSelectedTask(task)}
                  className={`group relative cursor-pointer p-4 transition-all hover:bg-white/5 ${
                    isSelected ? 'bg-blue-500/10' : ''
                  }`}
                >
                  <div className="flex items-start gap-4">
                    <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border ${config.border} ${config.bg}`}>
                      <Icon className={`h-5 w-5 ${config.color} ${config.animate ? 'animate-spin' : ''}`} />
                    </div>
                    
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <p className="truncate font-medium text-white group-hover:text-blue-400 transition-colors">
                          {task.description}
                        </p>
                        <ChevronRight className={`h-4 w-4 shrink-0 text-slate-600 transition-all ${
                          isSelected ? 'rotate-90 text-blue-400' : 'group-hover:text-slate-400'
                        }`} />
                      </div>
                      
                      <div className="mt-2 flex items-center gap-3 text-xs">
                        <span className={`rounded-full border px-2.5 py-1 font-semibold uppercase tracking-wider ${config.border} ${config.bg} ${config.color}`}>
                          {config.label}
                        </span>
                        <span className="text-slate-500">
                          {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
                        </span>
                        {task.metrics?.success_rate !== undefined && (
                          <span className={`font-semibold ${
                            task.metrics.success_rate > 0.8 ? 'text-green-400' : 'text-yellow-400'
                          }`}>
                            {(task.metrics.success_rate * 100).toFixed(0)}% success
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

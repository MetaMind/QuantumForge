import { create } from 'zustand'

interface Task {
  task_id: string
  description: string
  status: string
  steps: any[]
  final_output?: string
  metrics?: Record<string, number>
  created_at: string
}

interface Provider {
  provider: string
  available: boolean
  priority: number
  model: string
  avg_latency?: number
  success_count?: number
}

interface Store {
  tasks: Task[]
  providers: Provider[]
  selectedTask: Task | null
  isConnected: boolean
  addTask: (task: Task) => void
  updateTask: (task: Task) => void
  setSelectedTask: (task: Task | null) => void
  setProviders: (providers: Provider[]) => void
  setConnected: (connected: boolean) => void
}

export const useStore = create<Store>((set) => ({
  tasks: [],
  providers: [],
  selectedTask: null,
  isConnected: false,
  addTask: (task) => set((state) => ({ tasks: [task, ...state.tasks] })),
  updateTask: (task) => set((state) => ({
    tasks: state.tasks.map((t) => (t.task_id === task.task_id ? task : t)),
  })),
  setSelectedTask: (task) => set({ selectedTask: task }),
  setProviders: (providers) => set({ providers }),
  setConnected: (connected) => set({ isConnected: connected }),
}))

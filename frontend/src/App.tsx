import { useWebSocket } from './hooks/useWebSocket'
import { Header } from './components/Header'
import { TaskCreator } from './components/TaskCreator'
import { TaskList } from './components/TaskList'
import { TaskDetail } from './components/TaskDetail'
import { ProviderStatus } from './components/ProviderStatus'
import { MetricsDashboard } from './components/MetricsDashboard'

function App() {
  useWebSocket()

  return (
    <div className="min-h-screen font-sans antialiased" style={{ backgroundColor: '#06060f' }}>
      {/* Ambient background layer */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden" aria-hidden>
        <div className="absolute" style={{ top: '-200px', left: '-200px', width: '600px', height: '600px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(34,211,238,0.06) 0%, transparent 70%)' }} />
        <div className="absolute" style={{ top: '40%', right: '-200px', width: '500px', height: '500px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(167,139,250,0.06) 0%, transparent 70%)' }} />
        <div className="absolute" style={{ bottom: '-200px', left: '35%', width: '450px', height: '450px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(99,102,241,0.05) 0%, transparent 70%)' }} />
        <div className="bg-grid-overlay absolute inset-0" />
      </div>

      <Header />

      <main className="relative mx-auto px-4 py-8" style={{ maxWidth: '1600px' }}>
        <div className="mb-6">
          <MetricsDashboard />
        </div>

        {/* Two-column layout: sidebar + main */}
        <div className="flex gap-6" style={{ alignItems: 'flex-start' }}>
          {/* Left sidebar */}
          <div className="flex flex-col gap-5 shrink-0" style={{ width: '360px' }}>
            <TaskCreator />
            <ProviderStatus />
          </div>

          {/* Right: task list + detail side by side */}
          <div className="flex-1 grid gap-6" style={{ gridTemplateColumns: '1fr 1fr', minWidth: 0 }}>
            <TaskList />
            <TaskDetail />
          </div>
        </div>
      </main>
    </div>
  )
}

export default App

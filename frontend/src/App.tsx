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
    <div className="min-h-screen bg-background font-sans antialiased">
      <Header />
      
      <main className="container py-6 space-y-6">
        <MetricsDashboard />
        
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6">
            <TaskCreator />
            <ProviderStatus />
          </div>
          
          <div className="lg:col-span-2 space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              <TaskList />
              <TaskDetail />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App

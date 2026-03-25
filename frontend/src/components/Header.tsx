import { Cpu, Zap, Activity, Wifi } from 'lucide-react'
import { useStore } from '../store/useStore'

export function Header() {
  const { isConnected, providers } = useStore()
  const activeProviders = providers.filter(p => p.available).length

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/10 bg-slate-950/80 backdrop-blur-xl">
      <div className="container flex h-16 items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <div className="relative group">
            <div className="absolute -inset-1 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 opacity-75 blur group-hover:opacity-100 transition duration-1000 group-hover:duration-200 animate-pulse-glow" />
            <div className="relative flex h-10 w-10 items-center justify-center rounded-lg bg-slate-950 ring-1 ring-white/10">
              <Cpu className="h-6 w-6 text-blue-400" />
            </div>
          </div>
          
          <div>
            <h1 className="text-2xl font-bold gradient-text">
              QuantumForge
            </h1>
            <p className="text-xs text-slate-400 font-medium tracking-wider uppercase">
              AI Engineering Platform
            </p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3 px-4 py-2 rounded-full glass">
            <Zap className="h-4 w-4 text-yellow-400" />
            <span className="text-sm text-slate-300">
              <span className="font-bold text-white">{activeProviders}</span>
              <span className="text-slate-500">/</span>
              <span className="text-slate-400">{providers.length}</span> Providers
            </span>
          </div>
          
          <div className={`flex items-center gap-2 px-4 py-2 rounded-full border ${
            isConnected 
              ? 'bg-green-500/10 border-green-500/30 text-green-400' 
              : 'bg-red-500/10 border-red-500/30 text-red-400'
          }`}>
            {isConnected ? <Activity className="h-4 w-4 animate-pulse" /> : <Wifi className="h-4 w-4" />}
            <span className="text-sm font-semibold">
              {isConnected ? 'LIVE' : 'OFFLINE'}
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}

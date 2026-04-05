import { Cpu, Zap, Activity, WifiOff } from 'lucide-react'
import { useStore } from '../store/useStore'

export function Header() {
  const { isConnected, providers } = useStore()
  const activeProviders = providers.filter(p => p.available).length

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/[0.06]" style={{ backgroundColor: 'rgba(6,6,15,0.92)', backdropFilter: 'blur(24px)' }}>
      <div className="mx-auto flex h-16 max-w-[1600px] items-center justify-between px-6">

        {/* Logo */}
        <div className="flex items-center gap-4">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-xl"
            style={{ background: 'linear-gradient(135deg, #0891b2 0%, #7c3aed 100%)', boxShadow: '0 0 20px rgba(34,211,238,0.3)' }}
          >
            <Cpu className="h-5 w-5 text-white" />
          </div>

          <div>
            <h1 className="text-xl font-black tracking-tight leading-none" style={{ background: 'linear-gradient(135deg, #22d3ee 0%, #818cf8 50%, #e879f9 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
              QuantumForge
            </h1>
            <p className="text-[10px] font-semibold tracking-[0.18em] uppercase mt-0.5" style={{ color: 'rgba(255,255,255,0.3)' }}>
              AI Engineering Platform
            </p>
          </div>
        </div>

        {/* Right pills */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-full px-4 py-1.5" style={{ border: '1px solid rgba(251,191,36,0.25)', backgroundColor: 'rgba(251,191,36,0.08)' }}>
            <Zap className="h-3.5 w-3.5 text-amber-400" />
            <span className="text-xs font-semibold" style={{ color: 'rgba(253,230,138,0.8)' }}>
              <span className="text-amber-300 font-bold">{activeProviders}</span>
              <span style={{ color: 'rgba(255,255,255,0.25)', margin: '0 4px' }}>/</span>
              <span>{providers.length}</span>
              <span style={{ color: 'rgba(255,255,255,0.35)', marginLeft: 4 }}>providers</span>
            </span>
          </div>

          <div
            className="flex items-center gap-2 rounded-full px-4 py-1.5 transition-all duration-500"
            style={isConnected
              ? { border: '1px solid rgba(52,211,153,0.3)', backgroundColor: 'rgba(52,211,153,0.1)', color: '#34d399' }
              : { border: '1px solid rgba(251,113,133,0.3)', backgroundColor: 'rgba(251,113,133,0.1)', color: '#fb7185' }
            }
          >
            {isConnected ? (
              <>
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
                </span>
                <Activity className="h-3.5 w-3.5" />
                <span className="text-xs font-bold tracking-widest">LIVE</span>
              </>
            ) : (
              <>
                <WifiOff className="h-3.5 w-3.5" />
                <span className="text-xs font-bold tracking-widest">OFFLINE</span>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}

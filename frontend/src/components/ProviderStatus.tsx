import React, { useEffect } from 'react'
import { useQuery } from 'react-query'
import { Zap, Brain, Cpu, WifiOff, Server } from 'lucide-react'
import { useStore } from '../store/useStore'
import axios from 'axios'

const providerMeta: Record<string, { icon: React.ElementType; color: string; accent: string; bg: string }> = {
  openai:    { icon: Brain,   color: '#34d399', accent: '#34d399', bg: 'rgba(52,211,153,0.1)'   },
  groq:      { icon: Zap,    color: '#fbbf24', accent: '#fbbf24', bg: 'rgba(251,191,36,0.1)'   },
  anthropic: { icon: Brain,   color: '#a78bfa', accent: '#a78bfa', bg: 'rgba(167,139,250,0.1)'  },
  local:     { icon: Cpu,    color: '#22d3ee', accent: '#22d3ee', bg: 'rgba(34,211,238,0.1)'   },
  fallback:  { icon: WifiOff, color: '#fb7185', accent: '#fb7185', bg: 'rgba(251,113,133,0.1)'  },
}

export function ProviderStatus() {
  const { setProviders } = useStore()

  const { data: health } = useQuery(
    'providers',
    async () => {
      const res = await axios.get('/api/health/llm')
      return res.data
    },
    { refetchInterval: 30000 }
  )

  useEffect(() => {
    if (health) {
      setProviders(Object.entries(health).map(([key, value]: [string, any]) => ({ provider: key, ...value })))
    }
  }, [health, setProviders])

  if (!health) return null

  const entries = Object.entries(health) as [string, any][]

  return (
    <div className="relative overflow-hidden rounded-2xl" style={{ border: '1px solid rgba(255,255,255,0.07)', backgroundColor: '#0c0c1e' }}>
      <div className="absolute top-0 left-0 right-0 h-[1px]" style={{ background: 'linear-gradient(90deg, transparent, rgba(251,191,36,0.5), transparent)' }} />

      <div className="p-5">
        <div className="flex items-center gap-2 mb-4">
          <Server className="h-4 w-4 text-amber-400" />
          <h3 className="text-sm font-bold" style={{ color: 'rgba(255,255,255,0.8)' }}>LLM Providers</h3>
          <span className="ml-auto text-[10px] font-semibold uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.25)' }}>
            {entries.filter(([, d]) => d.available).length}/{entries.length} online
          </span>
        </div>

        <div className="space-y-2">
          {entries.map(([name, data]) => {
            const meta = providerMeta[name] ?? { icon: Cpu, color: 'rgba(255,255,255,0.5)', accent: '#fff', bg: 'rgba(255,255,255,0.05)' }
            const Icon = meta.icon
            const online = data.available

            return (
              <div
                key={name}
                className="flex items-center gap-3 rounded-xl px-3 py-2.5 cursor-default transition-all duration-200"
                style={{ border: '1px solid rgba(255,255,255,0.05)', backgroundColor: 'rgba(255,255,255,0.02)' }}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.backgroundColor = 'rgba(255,255,255,0.05)'; (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.1)' }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.backgroundColor = 'rgba(255,255,255,0.02)'; (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.05)' }}
              >
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg" style={{ backgroundColor: meta.bg }}>
                  <Icon className="h-4 w-4" style={{ color: meta.color }} />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold capitalize" style={{ color: 'rgba(255,255,255,0.8)' }}>{name}</span>
                    {data.model && (
                      <span className="truncate text-[10px] font-mono" style={{ color: 'rgba(255,255,255,0.25)' }}>{data.model}</span>
                    )}
                  </div>
                  <div className="text-[10px] mt-0.5" style={{ color: 'rgba(255,255,255,0.3)' }}>
                    {online ? `Latency: ${data.avg_latency?.toFixed(0) ?? 'N/A'} ms` : 'Unavailable'}
                  </div>
                </div>

                <div className="relative flex h-2 w-2 shrink-0">
                  {online && (
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full opacity-60" style={{ backgroundColor: meta.accent }} />
                  )}
                  <span className="relative inline-flex h-2 w-2 rounded-full" style={{ backgroundColor: online ? meta.accent : '#4b5563' }} />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

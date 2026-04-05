import { useMemo } from 'react'
import { useStore } from '../store/useStore'
import {
  AreaChart, Area,
  BarChart, Bar, Cell,
  XAxis, YAxis,
  CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { Activity, CheckCircle2, XCircle, Clock, TrendingUp } from 'lucide-react'

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-xl px-3 py-2 text-xs shadow-xl" style={{ border: '1px solid rgba(255,255,255,0.1)', backgroundColor: '#0d0d1f' }}>
      {label && <p className="text-white/40 mb-1">{label}</p>}
      {payload.map((p: any, i: number) => (
        <p key={i} style={{ color: p.color ?? p.fill }} className="font-semibold">
          {p.name ?? p.dataKey}: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}
        </p>
      ))}
    </div>
  )
}

const STAT_CARDS = [
  { key: 'total',          label: 'Total Tasks',   Icon: Activity,    accent: '#22d3ee', border: 'border-cyan-500/20',    bg: 'from-cyan-500/10 to-transparent'    },
  { key: 'avgSuccessRate', label: 'Success Rate',  Icon: TrendingUp,  accent: '#34d399', border: 'border-emerald-500/20', bg: 'from-emerald-500/10 to-transparent', fmt: (v: number) => `${(v * 100).toFixed(1)}%` },
  { key: 'pending',        label: 'Active',        Icon: Clock,       accent: '#a78bfa', border: 'border-violet-500/20',  bg: 'from-violet-500/10 to-transparent'  },
  { key: 'failed',         label: 'Failed',        Icon: XCircle,     accent: '#fb7185', border: 'border-rose-500/20',    bg: 'from-rose-500/10 to-transparent'    },
]

const BAR_COLORS = ['#34d399', '#a78bfa', '#fb7185']

export function MetricsDashboard() {
  const { tasks } = useStore()

  const stats = useMemo(() => {
    const total     = tasks.length
    const completed = tasks.filter(t => t.status === 'completed').length
    const failed    = tasks.filter(t => t.status === 'failed').length
    const pending   = tasks.filter(t => ['pending','planning','executing','evaluating','fixing'].includes(t.status)).length
    const avgSuccessRate = total > 0
      ? tasks.reduce((a, t) => a + (t.metrics?.success_rate || 0), 0) / total
      : 0
    return { total, completed, failed, pending, avgSuccessRate }
  }, [tasks])

  const barData = [
    { name: 'Done',   value: stats.completed },
    { name: 'Active', value: stats.pending   },
    { name: 'Failed', value: stats.failed    },
  ]

  const areaData = tasks.slice(-14).map((t, i) => ({
    i,
    score: (t.metrics?.success_rate || 0) * 100,
  }))

  return (
    <div className="animate-slide-up space-y-4">
      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {STAT_CARDS.map(({ key, label, Icon, accent, border: _border, bg: _bg, fmt }) => {
          const raw = stats[key as keyof typeof stats] as number
          const display = fmt ? fmt(raw) : String(raw)
          // derive rgba from accent hex for the gradient overlay
          const accentRgba = accent + '1a' // ~10% opacity
          return (
            <div
              key={key}
              className="stat-card relative overflow-hidden rounded-2xl p-5"
              style={{
                backgroundColor: '#0c0c1e',
                border: `1px solid ${accent}33`,
                background: `linear-gradient(135deg, ${accentRgba} 0%, #0c0c1e 60%)`,
              }}
            >
              <div
                className="pointer-events-none absolute -right-8 -top-8 h-28 w-28 rounded-full blur-2xl opacity-25"
                style={{ background: accent }}
              />
              <div className="relative flex items-start justify-between">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-widest mb-2" style={{ color: 'rgba(255,255,255,0.35)' }}>{label}</p>
                  <p className="text-3xl font-black" style={{ color: accent }}>{display}</p>
                </div>
                <div className="flex h-9 w-9 items-center justify-center rounded-xl" style={{ border: '1px solid rgba(255,255,255,0.07)', backgroundColor: 'rgba(255,255,255,0.04)' }}>
                  <Icon className="h-4 w-4" style={{ color: accent }} />
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Charts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl p-5" style={{ border: '1px solid rgba(255,255,255,0.06)', backgroundColor: '#0c0c1e' }}>
          <div className="flex items-center gap-2 mb-5">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <span className="text-sm font-semibold" style={{ color: 'rgba(255,255,255,0.7)' }}>Task Distribution</span>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={barData} barSize={40} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.04)" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: 'rgba(255,255,255,.3)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: 'rgba(255,255,255,.3)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,.03)' }} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {barData.map((_, i) => (
                  <Cell key={i} fill={BAR_COLORS[i]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-2xl p-5" style={{ border: '1px solid rgba(255,255,255,0.06)', backgroundColor: '#0c0c1e' }}>
          <div className="flex items-center gap-2 mb-5">
            <Activity className="h-4 w-4 text-cyan-400" />
            <span className="text-sm font-semibold" style={{ color: 'rgba(255,255,255,0.7)' }}>Success Rate Trend</span>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={areaData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="cyanGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#22d3ee" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#22d3ee" stopOpacity={0}    />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.04)" vertical={false} />
              <XAxis dataKey="i" hide />
              <YAxis tick={{ fill: 'rgba(255,255,255,.3)', fontSize: 11 }} axisLine={false} tickLine={false} domain={[0, 100]} />
              <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(34,211,238,.25)', strokeWidth: 1 }} />
              <Area
                type="monotone"
                dataKey="score"
                stroke="#22d3ee"
                strokeWidth={2}
                fill="url(#cyanGrad)"
                dot={false}
                activeDot={{ r: 4, fill: '#22d3ee', stroke: '#06060f', strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

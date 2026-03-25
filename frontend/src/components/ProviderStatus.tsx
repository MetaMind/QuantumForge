import { useEffect } from 'react'
import { useQuery } from 'react-query'
import { Zap, Brain, Cpu, WifiOff } from 'lucide-react'
import { useStore } from '../store/useStore'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import axios from 'axios'

const providerIcons = {
  openai: Brain,
  groq: Zap,
  anthropic: Brain,
  local: Cpu,
  fallback: WifiOff,
}

export function ProviderStatus() {
  const { setProviders } = useStore()

  const { data: health } = useQuery(
    'providers',
    async () => {
      const response = await axios.get('/api/health/llm')
      return response.data
    },
    { refetchInterval: 30000 }
  )

  useEffect(() => {
    if (health) {
      const providers = Object.entries(health).map(([key, value]: [string, any]) => ({
        provider: key,
        ...value,
      }))
      setProviders(providers)
    }
  }, [health, setProviders])

  if (!health) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Zap className="h-5 w-5 text-yellow-500" />
          LLM Providers
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {Object.entries(health).map(([name, data]: [string, any]) => {
            const Icon = providerIcons[name as keyof typeof providerIcons] || Cpu
            
            return (
              <div 
                key={name}
                className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-full ${data.available ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="font-medium capitalize flex items-center gap-2">
                      {name}
                      {data.model && (
                        <span className="text-xs text-muted-foreground font-normal">
                          {data.model}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {data.available ? (
                        <span>Avg latency: {data.avg_latency?.toFixed(0) || 'N/A'}ms</span>
                      ) : (
                        <span>Unavailable</span>
                      )}
                    </div>
                  </div>
                </div>
                <Badge variant={data.available ? 'success' : 'destructive'}>
                  {data.available ? 'Active' : 'Down'}
                </Badge>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

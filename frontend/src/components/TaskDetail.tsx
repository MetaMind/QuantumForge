import { useState } from 'react'
import Editor from '@monaco-editor/react'
import { Terminal, Code2, GitBranch, Activity, Cpu, CheckCircle2, XCircle } from 'lucide-react'
import { useStore } from '../store/useStore'
import { ScrollArea } from './ui/scroll-area'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './ui/accordion'

const tabs = [
  { id: 'code',      label: 'Code',      icon: Code2     },
  { id: 'execution', label: 'Execution', icon: Terminal  },
  { id: 'agents',    label: 'Agents',    icon: GitBranch },
]

export function TaskDetail() {
  const { selectedTask } = useStore()
  const [activeTab, setActiveTab] = useState('code')

  if (!selectedTask) {
    return (
      <div className="relative flex items-center justify-center overflow-hidden rounded-2xl" style={{ border: '1px solid rgba(255,255,255,0.07)', backgroundColor: '#0c0c1e', minHeight: '400px' }}>
        <div className="absolute top-0 left-0 right-0 h-[1px]" style={{ background: 'linear-gradient(90deg, transparent, rgba(34,211,238,0.3), transparent)' }} />
        <div className="text-center animate-slide-up">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl" style={{ border: '1px solid rgba(255,255,255,0.06)', backgroundColor: 'rgba(255,255,255,0.03)' }}>
            <Cpu className="h-7 w-7 animate-float" style={{ color: 'rgba(255,255,255,0.15)' }} />
          </div>
          <p className="text-sm" style={{ color: 'rgba(255,255,255,0.25)' }}>Select a task to inspect</p>
        </div>
      </div>
    )
  }

  const statusStyle =
    selectedTask.status === 'completed'
      ? { color: '#34d399', backgroundColor: 'rgba(52,211,153,0.1)', border: '1px solid rgba(52,211,153,0.25)' }
      : selectedTask.status === 'failed'
      ? { color: '#fb7185', backgroundColor: 'rgba(251,113,133,0.1)', border: '1px solid rgba(251,113,133,0.25)' }
      : { color: '#22d3ee', backgroundColor: 'rgba(34,211,238,0.1)', border: '1px solid rgba(34,211,238,0.25)' }

  return (
    <div className="relative flex flex-col overflow-hidden rounded-2xl" style={{ border: '1px solid rgba(255,255,255,0.07)', backgroundColor: '#0c0c1e', minHeight: '400px' }}>
      <div className="absolute top-0 left-0 right-0 h-[1px]" style={{ background: 'linear-gradient(90deg, transparent, rgba(34,211,238,0.4), transparent)' }} />

      {/* Header */}
      <div className="px-5 py-4" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
        <p className="text-sm font-semibold mb-2 line-clamp-2" style={{ color: 'rgba(255,255,255,0.8)' }}>{selectedTask.description}</p>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="rounded-md px-2 py-0.5 font-mono text-[10px]" style={{ border: '1px solid rgba(255,255,255,0.08)', backgroundColor: 'rgba(255,255,255,0.04)', color: 'rgba(255,255,255,0.35)' }}>
            {selectedTask.task_id}
          </span>
          <span className="rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider" style={statusStyle}>
            {selectedTask.status}
          </span>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 px-5 pt-2" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className="relative flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-t-lg transition-all duration-150"
            style={{ color: activeTab === id ? '#22d3ee' : 'rgba(255,255,255,0.3)' }}
          >
            <Icon className="h-3.5 w-3.5" />
            {label}
            {activeTab === id && (
              <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full" style={{ background: 'linear-gradient(90deg, #22d3ee, #a78bfa)' }} />
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden p-4">
        {activeTab === 'code' && (
          <div className="overflow-hidden rounded-xl" style={{ border: '1px solid rgba(255,255,255,0.06)', minHeight: '300px', height: '100%' }}>
            <Editor
              height="320px"
              defaultLanguage="python"
              value={selectedTask.final_output || '# Code will appear here...'}
              theme="vs-dark"
              options={{
                readOnly: true,
                minimap: { enabled: false },
                fontSize: 13,
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                automaticLayout: true,
                fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                padding: { top: 12, bottom: 12 },
              }}
            />
          </div>
        )}

        {activeTab === 'execution' && (
          <ScrollArea className="rounded-xl font-mono text-xs" style={{ maxHeight: '340px', border: '1px solid rgba(255,255,255,0.06)', backgroundColor: 'rgba(0,0,0,0.4)', padding: '16px' }}>
            <div className="space-y-4">
              {selectedTask.steps?.map((step: any, idx: number) => (
                <div key={idx} className="pl-4" style={{ borderLeft: '2px solid rgba(34,211,238,0.2)' }}>
                  <div className="flex items-center gap-2 mb-1" style={{ color: 'rgba(255,255,255,0.3)' }}>
                    <Activity className="h-3 w-3" style={{ color: 'rgba(34,211,238,0.6)' }} />
                    <span>Step {idx + 1}</span>
                    <span style={{ color: 'rgba(255,255,255,0.15)' }}>·</span>
                    <span style={{ color: step.status === 'completed' ? '#34d399' : '#fbbf24' }}>{step.status}</span>
                    {step.score && <><span style={{ color: 'rgba(255,255,255,0.15)' }}>·</span><span style={{ color: '#22d3ee' }}>{(step.score * 100).toFixed(1)}%</span></>}
                  </div>
                  <p className="mb-2" style={{ color: 'rgba(255,255,255,0.6)' }}>{step.description}</p>
                  {step.attempts?.map((attempt: any, aidx: number) => (
                    <div key={aidx} className="mt-2 rounded-lg p-2" style={{ backgroundColor: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
                      <div className="mb-1" style={{ color: 'rgba(255,255,255,0.25)' }}>Attempt {aidx + 1}</div>
                      {attempt.stderr && <div style={{ color: 'rgba(251,113,133,0.8)' }}>{attempt.stderr}</div>}
                      {attempt.stdout && <div style={{ color: 'rgba(52,211,153,0.8)' }}>{attempt.stdout}</div>}
                    </div>
                  ))}
                </div>
              ))}
              {!selectedTask.steps?.length && <p style={{ color: 'rgba(255,255,255,0.2)' }}>No execution data yet…</p>}
            </div>
          </ScrollArea>
        )}

        {activeTab === 'agents' && (
          <ScrollArea style={{ maxHeight: '340px' }}>
            <Accordion type="single" collapsible className="space-y-2">
              {selectedTask.steps?.map((step: any, idx: number) => (
                <AccordionItem key={idx} value={`step-${idx}`} className="overflow-hidden rounded-xl" style={{ border: '1px solid rgba(255,255,255,0.06)', backgroundColor: 'rgba(255,255,255,0.02)' }}>
                  <AccordionTrigger className="px-4 py-3 hover:no-underline transition-colors" style={{ backgroundColor: undefined }}>
                    <div className="flex items-center gap-3 text-left">
                      <div className="flex h-7 w-7 items-center justify-center rounded-lg text-xs font-bold" style={{ background: 'linear-gradient(135deg, rgba(34,211,238,0.2), rgba(167,139,250,0.2))', color: '#22d3ee' }}>
                        {idx + 1}
                      </div>
                      <div>
                        <p className="text-sm font-medium" style={{ color: 'rgba(255,255,255,0.75)' }}>{step.description}</p>
                        <p className="text-[10px]" style={{ color: 'rgba(255,255,255,0.25)' }}>{step.attempts?.length || 0} attempts</p>
                      </div>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="px-4 pb-3">
                    <div className="space-y-2 pl-10">
                      {step.attempts?.map((attempt: any, aidx: number) => (
                        <div key={aidx} className="flex items-center gap-3 rounded-lg px-3 py-2 text-xs" style={{ border: '1px solid rgba(255,255,255,0.05)', backgroundColor: 'rgba(255,255,255,0.02)' }}>
                          {attempt.success
                            ? <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-400" />
                            : <XCircle className="h-3.5 w-3.5 shrink-0 text-rose-400" />}
                          <span style={{ color: attempt.success ? '#34d399' : '#fb7185' }}>{attempt.success ? 'Success' : 'Failed'}</span>
                          <span style={{ color: 'rgba(255,255,255,0.25)' }}>exit {attempt.exit_code}</span>
                          <span style={{ color: 'rgba(255,255,255,0.25)' }}>{attempt.execution_time?.toFixed(2)}s</span>
                        </div>
                      ))}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
              {!selectedTask.steps?.length && <p className="px-2 text-xs" style={{ color: 'rgba(255,255,255,0.2)' }}>No agent data yet…</p>}
            </Accordion>
          </ScrollArea>
        )}
      </div>
    </div>
  )
}

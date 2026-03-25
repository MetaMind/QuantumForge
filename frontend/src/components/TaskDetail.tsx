import { useState } from 'react'
import Editor from '@monaco-editor/react'
import { 
  Terminal, 
  Code2, 
  GitBranch, 
  Activity,
  Cpu,
  Database
} from 'lucide-react'
import { useStore } from '../store/useStore'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { ScrollArea } from './ui/scroll-area'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './ui/accordion'

export function TaskDetail() {
  const { selectedTask } = useStore()
  const [activeTab, setActiveTab] = useState('code')

  if (!selectedTask) {
    return (
      <Card className="h-[600px] flex items-center justify-center border-dashed">
        <div className="text-center text-muted-foreground">
          <Cpu className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Select a task to view details</p>
        </div>
      </Card>
    )
  }

  return (
    <Card className="h-[600px] flex flex-col">
      <CardHeader className="border-b">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg mb-2">{selectedTask.description}</CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="font-mono text-xs">
                {selectedTask.task_id}
              </Badge>
              <Badge variant={
                selectedTask.status === 'completed' ? 'success' :
                selectedTask.status === 'failed' ? 'destructive' : 'default'
              }>
                {selectedTask.status}
              </Badge>
            </div>
          </div>
        </div>
      </CardHeader>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
        <TabsList className="mx-6 mt-6 grid w-auto grid-cols-3">
          <TabsTrigger value="code" className="gap-2">
            <Code2 className="h-4 w-4" />
            Generated Code
          </TabsTrigger>
          <TabsTrigger value="execution" className="gap-2">
            <Terminal className="h-4 w-4" />
            Execution Log
          </TabsTrigger>
          <TabsTrigger value="agents" className="gap-2">
            <GitBranch className="h-4 w-4" />
            Agent Flow
          </TabsTrigger>
        </TabsList>

        <CardContent className="flex-1 p-6 pt-2 overflow-hidden">
          <TabsContent value="code" className="h-full mt-0">
            <Editor
              height="100%"
              defaultLanguage="python"
              value={selectedTask.final_output || '# Code will appear here...'}
              theme="vs-dark"
              options={{
                readOnly: true,
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on',
                roundedSelection: false,
                scrollBeyondLastLine: false,
                automaticLayout: true,
              }}
            />
          </TabsContent>

          <TabsContent value="execution" className="h-full mt-0">
            <ScrollArea className="h-full rounded-md border bg-black/50 p-4 font-mono text-sm">
              <div className="space-y-4">
                {selectedTask.steps?.map((step: any, idx: number) => (
                  <div key={idx} className="border-l-2 border-primary/30 pl-4">
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
                      <Activity className="h-3 w-3" />
                      <span>Step {idx + 1}</span>
                      <span>•</span>
                      <span>{step.status}</span>
                      {step.score && (
                        <>
                          <span>•</span>
                          <span>Score: {(step.score * 100).toFixed(1)}%</span>
                        </>
                      )}
                    </div>
                    <p className="text-sm mb-2">{step.description}</p>
                    {step.attempts?.map((attempt: any, aidx: number) => (
                      <div key={aidx} className="mt-2 text-xs bg-background/50 p-2 rounded">
                        <div className="text-muted-foreground">Attempt {aidx + 1}:</div>
                        {attempt.stderr && (
                          <div className="text-red-400 mt-1">{attempt.stderr}</div>
                        )}
                        {attempt.stdout && (
                          <div className="text-green-400 mt-1">{attempt.stdout}</div>
                        )}
                      </div>
                    ))}
                  </div>
                ))}
                {!selectedTask.steps?.length && (
                  <div className="text-muted-foreground">No execution data available...</div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="agents" className="h-full mt-0 overflow-auto">
            <div className="space-y-4">
              <Accordion type="single" collapsible>
                {selectedTask.steps?.map((step: any, idx: number) => (
                  <AccordionItem key={idx} value={`step-${idx}`}>
                    <AccordionTrigger className="hover:no-underline">
                      <div className="flex items-center gap-3 text-left">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-bold">
                          {idx + 1}
                        </div>
                        <div>
                          <div className="font-medium">{step.description}</div>
                          <div className="text-xs text-muted-foreground">
                            {step.attempts?.length || 0} attempts
                          </div>
                        </div>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="pl-11 space-y-2">
                        {step.attempts?.map((attempt: any, aidx: number) => (
                          <div key={aidx} className="flex items-center gap-3 text-sm p-2 rounded bg-muted">
                            <Badge variant={attempt.success ? 'success' : 'destructive'} className="text-[10px]">
                              {attempt.success ? 'Success' : 'Failed'}
                            </Badge>
                            <span className="text-muted-foreground">
                              Exit code: {attempt.exit_code}
                            </span>
                            <span className="text-muted-foreground">
                              Time: {attempt.execution_time?.toFixed(2)}s
                            </span>
                          </div>
                        ))}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </div>
          </TabsContent>
        </CardContent>
      </Tabs>
    </Card>
  )
}

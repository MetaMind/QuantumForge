import { useEffect, useRef } from 'react'
import { useStore } from '../store/useStore'

export const useWebSocket = () => {
  const ws = useRef<WebSocket | null>(null)
  const { setConnected, updateTask, addTask } = useStore()

  useEffect(() => {
    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/ws/tasks`
      
      ws.current = new WebSocket(wsUrl)

      ws.current.onopen = () => {
        console.log('WebSocket connected')
        setConnected(true)
      }

      ws.current.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        if (data.type === 'task_update') {
          updateTask(data.task)
        } else if (data.type === 'task_created') {
          addTask(data.task)
        }
      }

      ws.current.onclose = () => {
        console.log('WebSocket disconnected')
        setConnected(false)
        setTimeout(connect, 3000)
      }

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    }

    connect()

    return () => {
      ws.current?.close()
    }
  }, [setConnected, updateTask, addTask])

  return ws.current
}

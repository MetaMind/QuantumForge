import { useEffect, useRef } from 'react'
import { useStore } from '../store/useStore'

const BASE_DELAY_MS = 1000
const MAX_DELAY_MS = 30000

export const useWebSocket = () => {
  const ws = useRef<WebSocket | null>(null)
  const reconnectAttempt = useRef(0)
  const { setConnected, updateTask, addTask } = useStore()

  useEffect(() => {
    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/ws/tasks`

      ws.current = new WebSocket(wsUrl)

      ws.current.onopen = () => {
        console.log('WebSocket connected')
        reconnectAttempt.current = 0  // reset backoff on successful connection
        setConnected(true)
      }

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'task_update') {
            updateTask(data.task)
          } else if (data.type === 'task_created') {
            addTask(data.task)
          }
        } catch (err) {
          console.error('WebSocket message parse error:', err)
          // return early — do not rethrow, keep connection alive
        }
      }

      ws.current.onclose = () => {
        console.log('WebSocket disconnected')
        setConnected(false)
        const delay = Math.min(BASE_DELAY_MS * 2 ** reconnectAttempt.current, MAX_DELAY_MS)
        reconnectAttempt.current += 1
        console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempt.current})`)
        setTimeout(connect, delay)
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

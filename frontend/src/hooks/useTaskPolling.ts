import { useState, useEffect, useRef } from 'react'
import { getTask } from '../api/tasks'
import type { TaskResponse } from '../types/api'
import { isTerminalStatus } from '../types/domain'

interface UseTaskPollingResult {
  task: TaskResponse | null
  isPolling: boolean
  error: string | null
}

export function useTaskPolling(
  taskId: string | null,
  intervalMs = 2000,
): UseTaskPollingResult {
  const [task, setTask] = useState<TaskResponse | null>(null)
  const [isPolling, setIsPolling] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!taskId) {
      setTask(null)
      setIsPolling(false)
      setError(null)
      return
    }

    setIsPolling(true)
    setError(null)

    async function poll() {
      if (!taskId) return
      try {
        const result = await getTask(taskId)
        setTask(result)
        if (isTerminalStatus(result.status)) {
          setIsPolling(false)
          if (intervalRef.current) {
            clearInterval(intervalRef.current)
            intervalRef.current = null
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : '轮询失败')
        setIsPolling(false)
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
          intervalRef.current = null
        }
      }
    }

    void poll()
    intervalRef.current = setInterval(() => { void poll() }, intervalMs)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [taskId, intervalMs])

  return { task, isPolling, error }
}

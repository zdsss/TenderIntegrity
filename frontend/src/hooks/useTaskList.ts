import { useState, useEffect, useCallback } from 'react'
import { listTasks, deleteTask } from '../api/tasks'
import type { TaskResponse } from '../types/api'

interface UseTaskListResult {
  tasks: TaskResponse[]
  loading: boolean
  error: string | null
  total: number
  page: number
  pageSize: number
  setPage: (page: number) => void
  refresh: () => void
  remove: (taskId: string) => Promise<void>
}

export function useTaskList(defaultPageSize = 10): UseTaskListResult {
  const [tasks, setTasks] = useState<TaskResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const pageSize = defaultPageSize

  const fetchTasks = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const offset = (page - 1) * pageSize
      const result = await listTasks(offset, pageSize)
      setTasks(result)
      // Backend doesn't return total; use length + offset as approximation
      setTotal(result.length < pageSize ? offset + result.length : offset + pageSize + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }, [page, pageSize])

  useEffect(() => {
    void fetchTasks()
  }, [fetchTasks])

  async function remove(taskId: string) {
    await deleteTask(taskId)
    await fetchTasks()
  }

  return {
    tasks,
    loading,
    error,
    total,
    page,
    pageSize,
    setPage,
    refresh: () => { void fetchTasks() },
    remove,
  }
}

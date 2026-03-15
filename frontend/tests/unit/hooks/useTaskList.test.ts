import { renderHook, act, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { useTaskList } from '../../../src/hooks/useTaskList'

vi.mock('../../../src/api/tasks', () => ({
  listTasks: vi.fn(),
  deleteTask: vi.fn(),
}))

import { listTasks, deleteTask } from '../../../src/api/tasks'
const mockList = vi.mocked(listTasks)
const mockDelete = vi.mocked(deleteTask)

const SAMPLE_TASKS = [
  { task_id: 't1', status: 'done' as const, progress: 1 },
  { task_id: 't2', status: 'running' as const, progress: 0.5 },
]

describe('useTaskList', () => {
  beforeEach(() => {
    mockList.mockReset()
    mockDelete.mockReset()
  })

  it('fetches tasks on mount', async () => {
    mockList.mockResolvedValue(SAMPLE_TASKS)
    const { result } = renderHook(() => useTaskList())
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.tasks).toHaveLength(2)
    expect(result.current.tasks[0].task_id).toBe('t1')
  })

  it('sets error on fetch failure', async () => {
    mockList.mockRejectedValue(new Error('服务不可用'))
    const { result } = renderHook(() => useTaskList())
    await waitFor(() => expect(result.current.error).toBe('服务不可用'))
  })

  it('removes task and refreshes list', async () => {
    mockList.mockResolvedValue(SAMPLE_TASKS)
    mockDelete.mockResolvedValue()

    const { result } = renderHook(() => useTaskList())
    await waitFor(() => expect(result.current.tasks).toHaveLength(2))

    mockList.mockResolvedValue([SAMPLE_TASKS[1]])
    await act(async () => {
      await result.current.remove('t1')
    })

    expect(mockDelete).toHaveBeenCalledWith('t1')
    await waitFor(() => expect(result.current.tasks).toHaveLength(1))
  })
})

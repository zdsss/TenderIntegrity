import { renderHook, act, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { useTaskPolling } from '../../../src/hooks/useTaskPolling'

vi.mock('../../../src/api/tasks', () => ({
  getTask: vi.fn(),
}))

import { getTask } from '../../../src/api/tasks'
const mockGetTask = vi.mocked(getTask)

describe('useTaskPolling', () => {
  beforeEach(() => {
    mockGetTask.mockReset()
  })

  it('does not poll when taskId is null', () => {
    const { result } = renderHook(() => useTaskPolling(null))
    expect(result.current.task).toBeNull()
    expect(result.current.isPolling).toBe(false)
  })

  it('starts polling when taskId is provided', async () => {
    mockGetTask.mockResolvedValue({
      task_id: 'abc',
      status: 'running',
      progress: 0.5,
    })

    const { result } = renderHook(() => useTaskPolling('abc', 50))

    await waitFor(() => expect(result.current.task).not.toBeNull(), { timeout: 3000 })
    expect(result.current.isPolling).toBe(true)
    expect(result.current.task?.status).toBe('running')
  })

  it('stops polling on done status', async () => {
    mockGetTask.mockResolvedValue({
      task_id: 'abc',
      status: 'done',
      progress: 1.0,
    })

    const { result } = renderHook(() => useTaskPolling('abc', 50))

    await waitFor(() => expect(result.current.isPolling).toBe(false), { timeout: 3000 })
    expect(result.current.task?.status).toBe('done')
  })

  it('stops polling on error status', async () => {
    mockGetTask.mockResolvedValue({
      task_id: 'abc',
      status: 'error',
      progress: 0,
      error_message: '处理失败',
    })

    const { result } = renderHook(() => useTaskPolling('abc', 50))

    await waitFor(() => expect(result.current.isPolling).toBe(false), { timeout: 3000 })
    expect(result.current.task?.status).toBe('error')
  })

  it('sets error state on API failure', async () => {
    mockGetTask.mockRejectedValue(new Error('网络错误'))

    const { result } = renderHook(() => useTaskPolling('abc', 50))

    await waitFor(() => expect(result.current.error).toBe('网络错误'), { timeout: 3000 })
    expect(result.current.isPolling).toBe(false)
  })

  it('polls multiple times while running', async () => {
    let callCount = 0
    mockGetTask.mockImplementation(async () => {
      callCount++
      return { task_id: 'abc', status: 'running' as const, progress: 0.2 }
    })

    renderHook(() => useTaskPolling('abc', 50))

    await waitFor(() => expect(callCount).toBeGreaterThanOrEqual(2), { timeout: 3000 })
  })

  it('cleans up interval on unmount', async () => {
    mockGetTask.mockResolvedValue({
      task_id: 'abc',
      status: 'running',
      progress: 0.5,
    })

    const { result, unmount } = renderHook(() => useTaskPolling('abc', 50))
    await waitFor(() => expect(result.current.task).not.toBeNull(), { timeout: 3000 })

    const callsBefore = mockGetTask.mock.calls.length
    unmount()
    await act(async () => {
      await new Promise((r) => setTimeout(r, 150))
    })
    // After unmount, no more calls should happen
    expect(mockGetTask.mock.calls.length).toBe(callsBefore)
  })
})

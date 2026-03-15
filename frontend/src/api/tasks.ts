import type { TaskCreateRequest, TaskResponse } from '../types/api'
import client from './client'

export async function createTask(request: TaskCreateRequest): Promise<TaskResponse> {
  const response = await client.post<TaskResponse>('/tasks', request)
  return response.data
}

export async function getTask(taskId: string): Promise<TaskResponse> {
  const response = await client.get<TaskResponse>(`/tasks/${taskId}`)
  return response.data
}

export async function listTasks(offset = 0, limit = 20): Promise<TaskResponse[]> {
  const response = await client.get<TaskResponse[]>('/tasks', {
    params: { offset, limit },
  })
  return response.data
}

export async function deleteTask(taskId: string): Promise<void> {
  await client.delete(`/tasks/${taskId}`)
}

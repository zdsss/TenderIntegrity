import type { RiskReportResponse } from '../types/api'
import client from './client'

export async function getReport(taskId: string): Promise<RiskReportResponse> {
  const response = await client.get<RiskReportResponse>(`/tasks/${taskId}/report`)
  return response.data
}

export async function downloadFile(taskId: string, format: 'csv' | 'pdf'): Promise<void> {
  const response = await client.get(`/tasks/${taskId}/report/${format}`, {
    responseType: 'blob',
  })
  const url = URL.createObjectURL(response.data as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `report_${taskId}.${format}`
  a.click()
  URL.revokeObjectURL(url)
}

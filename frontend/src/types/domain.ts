import type { RiskLevel, TaskStatus } from './api'

// ── Risk level ─────────────────────────────────────────────────────────────

export const RISK_LEVEL_COLOR: Record<RiskLevel, string> = {
  high: 'red',
  medium: 'orange',
  low: 'blue',
  none: 'default',
}

export const RISK_LEVEL_LABEL_ZH: Record<RiskLevel, string> = {
  high: '高风险',
  medium: '中风险',
  low: '低风险',
  none: '无风险',
}

// ── Task status ────────────────────────────────────────────────────────────

export const TASK_STATUS_COLOR: Record<TaskStatus, string> = {
  pending: 'default',
  running: 'processing',
  done: 'success',
  error: 'error',
}

export const TASK_STATUS_LABEL_ZH: Record<TaskStatus, string> = {
  pending: '排队中',
  running: '检测中',
  done: '已完成',
  error: '失败',
}

// ── Risk types ─────────────────────────────────────────────────────────────

export const RISK_TYPE_LABEL_ZH: Record<string, string> = {
  verbatim_copy: '逐字抄袭',
  semantic_paraphrase: '语义改写',
  structural_similarity: '结构雷同',
  price_coordination: '价格协调',
  contact_information: '联系方式雷同',
  unknown: '未知类型',
}

export function getRiskTypeLabel(riskType: string): string {
  return RISK_TYPE_LABEL_ZH[riskType] ?? riskType
}

// ── Terminal states ────────────────────────────────────────────────────────

export const TERMINAL_STATUSES: TaskStatus[] = ['done', 'error']

export function isTerminalStatus(status: TaskStatus): boolean {
  return TERMINAL_STATUSES.includes(status)
}

import { Badge } from 'antd'
import type { BadgeProps } from 'antd'
import type { TaskStatus } from '../types/api'
import { TASK_STATUS_COLOR, TASK_STATUS_LABEL_ZH } from '../types/domain'

interface Props {
  status: TaskStatus | string
}

export default function StatusBadge({ status }: Props) {
  const key = status as TaskStatus
  const color = (TASK_STATUS_COLOR[key] ?? 'default') as BadgeProps['status']
  const label = TASK_STATUS_LABEL_ZH[key] ?? status
  return <Badge status={color} text={label} />
}

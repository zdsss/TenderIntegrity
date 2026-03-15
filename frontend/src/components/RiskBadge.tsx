import { Tag } from 'antd'
import type { RiskLevel } from '../types/api'
import { RISK_LEVEL_COLOR, RISK_LEVEL_LABEL_ZH } from '../types/domain'

interface Props {
  level: RiskLevel | string
}

export default function RiskBadge({ level }: Props) {
  const key = level as RiskLevel
  const color = RISK_LEVEL_COLOR[key] ?? 'default'
  const label = RISK_LEVEL_LABEL_ZH[key] ?? level
  return <Tag color={color}>{label}</Tag>
}

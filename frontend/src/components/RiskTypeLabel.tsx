import { Tag } from 'antd'
import { getRiskTypeLabel } from '../types/domain'

interface Props {
  riskType: string
}

export default function RiskTypeLabel({ riskType }: Props) {
  return <Tag>{getRiskTypeLabel(riskType)}</Tag>
}

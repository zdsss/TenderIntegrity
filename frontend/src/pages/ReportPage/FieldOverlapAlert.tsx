import { Alert, Space, Tag, Typography } from 'antd'
import type { FieldOverlap } from '../../types/api'

const { Text } = Typography

const FIELD_LABELS: Record<string, string> = {
  phone: '电话',
  email: '邮箱',
  person: '联系人',
  company: '公司',
  project: '项目',
}

interface Props {
  overlaps: FieldOverlap[]
}

export default function FieldOverlapAlert({ overlaps }: Props) {
  if (!overlaps || overlaps.length === 0) return null

  const description = (
    <Space direction="vertical" size={4}>
      {overlaps.map((o, idx) => (
        <Space key={idx} size={8} wrap>
          <Tag color={o.overlap_type === 'exact' ? 'error' : 'warning'}>
            {FIELD_LABELS[o.field_type] ?? o.field_type}
            {o.overlap_type === 'fuzzy' ? '（模糊）' : '（精确）'}
          </Tag>
          <Text>{o.risk_note}</Text>
        </Space>
      ))}
    </Space>
  )

  return (
    <Alert
      type="error"
      showIcon
      message={`发现 ${overlaps.length} 项关键字段重叠（围标高风险信号）`}
      description={description}
      style={{ marginBottom: 16 }}
    />
  )
}

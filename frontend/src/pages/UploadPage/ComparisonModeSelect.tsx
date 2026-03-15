import { Radio, Space, Typography } from 'antd'
import type { ComparisonMode } from '../../types/api'

const { Text } = Typography

interface Props {
  value: ComparisonMode
  onChange: (mode: ComparisonMode) => void
}

export default function ComparisonModeSelect({ value, onChange }: Props) {
  return (
    <Space orientation="vertical" style={{ marginBottom: 16 }}>
      <Text strong>比对模式</Text>
      <Radio.Group
        value={value}
        onChange={(e) => onChange(e.target.value as ComparisonMode)}
        optionType="button"
        buttonStyle="solid"
      >
        <Radio.Button value="pairwise">两两比对</Radio.Button>
        <Radio.Button value="all_vs_all">全部对比</Radio.Button>
      </Radio.Group>
    </Space>
  )
}

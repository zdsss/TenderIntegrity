import { Table } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import RiskBadge from '../../components/RiskBadge'
import RiskTypeLabel from '../../components/RiskTypeLabel'
import ScoreBar from '../../components/ScoreBar'
import ExpandedPairDetail from './ExpandedPairDetail'
import type { RiskPairDetail } from '../../types/api'

interface Props {
  pairs: RiskPairDetail[]
}

const columns: ColumnsType<RiskPairDetail> = [
  {
    title: '风险等级',
    dataIndex: 'risk_level',
    key: 'risk_level',
    render: (level: string) => <RiskBadge level={level} />,
  },
  {
    title: '风险类型',
    dataIndex: 'risk_type',
    key: 'risk_type',
    render: (type: string) => <RiskTypeLabel riskType={type} />,
  },
  {
    title: '综合分值',
    dataIndex: 'final_score',
    key: 'final_score',
    render: (score: number) => <ScoreBar score={score} />,
  },
  {
    title: '向量相似度',
    dataIndex: 'vector_similarity',
    key: 'vector_similarity',
    render: (v: number) => `${(v * 100).toFixed(1)}%`,
  },
  {
    title: '关键词重叠',
    dataIndex: 'keyword_overlap',
    key: 'keyword_overlap',
    render: (v: number) => `${(v * 100).toFixed(1)}%`,
  },
]

export default function RiskPairsTable({ pairs }: Props) {
  return (
    <Table
      columns={columns}
      dataSource={pairs}
      rowKey="pair_id"
      expandable={{
        expandedRowRender: (pair) => <ExpandedPairDetail pair={pair} />,
      }}
      pagination={{ pageSize: 10 }}
    />
  )
}

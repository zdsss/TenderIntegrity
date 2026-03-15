import { Button, Popconfirm, Space, Table, Tooltip, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router-dom'
import RiskBadge from '../../components/RiskBadge'
import StatusBadge from '../../components/StatusBadge'
import type { TaskResponse } from '../../types/api'

const { Text } = Typography

interface Props {
  tasks: TaskResponse[]
  loading: boolean
  total: number
  page: number
  pageSize: number
  onPageChange: (page: number) => void
  onDelete: (taskId: string) => Promise<void>
}

function truncateId(id: string): string {
  return id.length > 12 ? `${id.slice(0, 12)}…` : id
}

export default function TaskTable({
  tasks,
  loading,
  total,
  page,
  pageSize,
  onPageChange,
  onDelete,
}: Props) {
  const navigate = useNavigate()

  const columns: ColumnsType<TaskResponse> = [
    {
      title: '任务 ID',
      dataIndex: 'task_id',
      key: 'task_id',
      render: (id: string) => (
        <Tooltip title={id}>
          <Text code>{truncateId(id)}</Text>
        </Tooltip>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (ts: string | null) =>
        ts ? dayjs(ts).format('YYYY-MM-DD HH:mm') : '—',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => <StatusBadge status={status} />,
    },
    {
      title: '风险等级',
      dataIndex: 'overall_risk_level',
      key: 'overall_risk_level',
      render: (level: string | null) =>
        level ? <RiskBadge level={level} /> : '—',
    },
    {
      title: '雷同率',
      dataIndex: 'overall_similarity_rate',
      key: 'overall_similarity_rate',
      render: (rate: number | null) =>
        rate != null ? `${(rate * 100).toFixed(1)}%` : '—',
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            disabled={record.status !== 'done'}
            onClick={() => navigate(`/tasks/${record.task_id}/report`)}
          >
            查看报告
          </Button>
          <Popconfirm
            title="确认删除此任务？"
            onConfirm={() => onDelete(record.task_id)}
            okText="删除"
            cancelText="取消"
          >
            <Button type="link" size="small" danger>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <Table
      columns={columns}
      dataSource={tasks}
      rowKey="task_id"
      loading={loading}
      pagination={{
        current: page,
        pageSize,
        total,
        onChange: onPageChange,
        showSizeChanger: false,
      }}
    />
  )
}

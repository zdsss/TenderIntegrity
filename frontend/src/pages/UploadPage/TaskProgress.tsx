import { Progress, Alert, Typography, Flex } from 'antd'
import { LoadingOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import type { TaskResponse } from '../../types/api'
import { TASK_STATUS_LABEL_ZH } from '../../types/domain'

const { Text } = Typography

interface Props {
  task: TaskResponse
  isPolling: boolean
}

export default function TaskProgress({ task, isPolling }: Props) {
  const statusLabel = TASK_STATUS_LABEL_ZH[task.status] ?? task.status

  if (task.status === 'error') {
    return (
      <Alert
        type="error"
        icon={<CloseCircleOutlined />}
        showIcon
        title="检测失败"
        description={task.error_message ?? '未知错误'}
      />
    )
  }

  if (task.status === 'done') {
    return (
      <Alert
        type="success"
        icon={<CheckCircleOutlined />}
        showIcon
        title="检测完成，正在跳转报告…"
      />
    )
  }

  return (
    <Flex vertical style={{ width: '100%' }} gap={8}>
      <Flex align="center" gap={8}>
        {isPolling && <LoadingOutlined />}
        <Text>{statusLabel}</Text>
      </Flex>
      <Progress percent={Math.round(task.progress * 100)} status="active" />
    </Flex>
  )
}

import { Card, Alert } from 'antd'
import { useTaskList } from '../../hooks/useTaskList'
import TaskTable from './TaskTable'

export default function TaskHistoryPage() {
  const { tasks, loading, error, total, page, pageSize, setPage, remove } = useTaskList()

  return (
    <Card title="历史记录">
      {error && (
        <Alert type="error" title={error} style={{ marginBottom: 16 }} />
      )}
      <TaskTable
        tasks={tasks}
        loading={loading}
        total={total}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onDelete={remove}
      />
    </Card>
  )
}

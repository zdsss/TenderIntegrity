import { useEffect, useRef } from 'react'
import { Alert, Button, Card, Divider, Space, Spin, message } from 'antd'
import { useNavigate } from 'react-router-dom'
import UploadZone from './UploadZone'
import FileList from './FileList'
import ComparisonModeSelect from './ComparisonModeSelect'
import TaskProgress from './TaskProgress'
import { useUploadSession } from '../../context/UploadSessionContext'
import { useTaskPolling } from '../../hooks/useTaskPolling'
import { createTask } from '../../api/tasks'
import { useState } from 'react'
import type { ComparisonMode } from '../../types/api'

export default function UploadPage() {
  const navigate = useNavigate()
  const { files, upload, remove, clear, taskId, setTaskId } = useUploadSession()
  const [mode, setMode] = useState<ComparisonMode>('pairwise')
  const [creating, setCreating] = useState(false)
  const { task, isPolling, error: pollingError } = useTaskPolling(taskId)
  const pollErrorCount = useRef(0)

  const uploadedDocIds = files
    .filter((f) => !f.uploading && !f.error && f.response)
    .map((f) => f.response!.doc_id)

  const canStart = uploadedDocIds.length >= 2 && !taskId

  async function handleStart() {
    if (!canStart) return
    setCreating(true)
    try {
      const created = await createTask({ doc_ids: uploadedDocIds, comparison_mode: mode })
      setTaskId(created.task_id)
    } catch (err) {
      void message.error(err instanceof Error ? err.message : '创建任务失败')
    } finally {
      setCreating(false)
    }
  }

  useEffect(() => {
    if (task?.status === 'done') {
      setTimeout(() => {
        navigate(`/tasks/${task.task_id}/report`)
        setTaskId(null)
        clear()
      }, 1000)
    }
  }, [task, navigate, clear, setTaskId])

  useEffect(() => {
    if (pollingError) {
      pollErrorCount.current += 1
      if (pollErrorCount.current >= 3) {
        pollErrorCount.current = 0
        setTaskId(null)
      }
    } else {
      pollErrorCount.current = 0
    }
  }, [pollingError, setTaskId])

  return (
    <Card title="上传标书文件">
      <UploadZone
        onFileSelected={(f) => { void upload(f) }}
        disabled={!!taskId}
      />
      <FileList files={files} onRemove={remove} />

      {files.length > 0 && (
        <>
          <Divider />
          <ComparisonModeSelect value={mode} onChange={setMode} />
          <Space>
            <Button
              type="primary"
              onClick={() => { void handleStart() }}
              loading={creating}
              disabled={!canStart}
            >
              开始检测
            </Button>
            {!taskId && (
              <Button onClick={clear} disabled={creating}>
                清空列表
              </Button>
            )}
          </Space>
        </>
      )}

      {(taskId || task) && (
        <>
          <Divider />
          {task
            ? <TaskProgress task={task} isPolling={isPolling} />
            : <Spin description="创建任务中…" />
          }
        </>
      )}

      {pollingError && (
        <Alert
          type="error"
          title={`轮询失败: ${pollingError}`}
          style={{ marginTop: 16 }}
        />
      )}
    </Card>
  )
}

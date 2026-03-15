import { Button, Space, message } from 'antd'
import { DownloadOutlined } from '@ant-design/icons'
import { downloadFile } from '../api/reports'

interface Props {
  taskId: string
}

export default function ExportButtons({ taskId }: Props) {
  async function handleDownload(format: 'csv' | 'pdf') {
    try {
      await downloadFile(taskId, format)
    } catch {
      void message.error(`下载 ${format.toUpperCase()} 失败`)
    }
  }

  return (
    <Space>
      <Button
        icon={<DownloadOutlined />}
        onClick={() => { void handleDownload('csv') }}
      >
        导出 CSV
      </Button>
      <Button
        icon={<DownloadOutlined />}
        onClick={() => { void handleDownload('pdf') }}
      >
        导出 PDF
      </Button>
    </Space>
  )
}

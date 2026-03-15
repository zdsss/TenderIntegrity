import { Button, Flex, Tag, Typography, Spin } from 'antd'
import { DeleteOutlined, CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import type { UploadedFile } from '../../hooks/useDocumentUpload'

const { Text } = Typography

interface Props {
  files: UploadedFile[]
  onRemove: (uid: string) => void
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function truncateId(id: string): string {
  return id.length > 12 ? `${id.slice(0, 8)}…` : id
}

export default function FileList({ files, onRemove }: Props) {
  if (files.length === 0) return null

  return (
    <Flex vertical gap={4} style={{ marginTop: 8, border: '1px solid #f0f0f0', borderRadius: 6 }}>
      {files.map((item, idx) => (
        <Flex
          key={item.uid}
          align="center"
          justify="space-between"
          style={{
            padding: '6px 12px',
            borderBottom: idx < files.length - 1 ? '1px solid #f0f0f0' : undefined,
          }}
        >
          <Flex align="center" gap={8} style={{ minWidth: 0 }}>
            {item.uploading ? (
              <Spin size="small" />
            ) : item.error ? (
              <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
            ) : (
              <CheckCircleOutlined style={{ color: '#52c41a' }} />
            )}
            <Flex vertical style={{ minWidth: 0 }}>
              <Text ellipsis={{ tooltip: item.file.name }} style={{ maxWidth: 200 }}>
                {item.file.name}
              </Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {formatSize(item.file.size)}
                {item.response && (
                  <Tag style={{ marginLeft: 8 }} color="blue">
                    ID: {truncateId(item.response.doc_id)}
                  </Tag>
                )}
                {item.error && (
                  <Tag style={{ marginLeft: 8 }} color="red">
                    {item.error}
                  </Tag>
                )}
              </Text>
            </Flex>
          </Flex>
          <Button
            type="text"
            danger
            size="small"
            icon={<DeleteOutlined />}
            onClick={() => onRemove(item.uid)}
          />
        </Flex>
      ))}
    </Flex>
  )
}

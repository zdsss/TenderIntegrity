import { Upload, message } from 'antd'
import { InboxOutlined } from '@ant-design/icons'
import type { UploadProps } from 'antd'

const { Dragger } = Upload

interface Props {
  onFileSelected: (file: File) => void
  disabled?: boolean
}

export default function UploadZone({ onFileSelected, disabled }: Props) {
  const props: UploadProps = {
    name: 'file',
    multiple: true,
    accept: '.pdf,.docx,.doc,.txt',
    disabled,
    beforeUpload: (file) => {
      const allowedExts = ['.pdf', '.docx', '.doc', '.txt']
      const ext = file.name.split('.').pop()?.toLowerCase() ?? ''
      if (!allowedExts.includes(`.${ext}`)) {
        void message.error(`不支持的文件类型: ${ext}`)
        return Upload.LIST_IGNORE
      }
      onFileSelected(file)
      return false  // prevent default upload behaviour
    },
    showUploadList: false,
  }

  return (
    <Dragger {...props} style={{ marginBottom: 16 }}>
      <p className="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
      <p className="ant-upload-hint">
        支持 PDF、Word（.docx/.doc）、TXT 格式，可同时选择多个文件
      </p>
    </Dragger>
  )
}

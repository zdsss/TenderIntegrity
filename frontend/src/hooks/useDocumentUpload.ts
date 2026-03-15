import { useState } from 'react'
import { uploadDocument } from '../api/documents'
import type { DocumentUploadResponse } from '../types/api'

export interface UploadedFile {
  uid: string
  file: File
  response?: DocumentUploadResponse
  error?: string
  uploading: boolean
}

interface UseDocumentUploadResult {
  files: UploadedFile[]
  upload: (file: File) => Promise<void>
  remove: (uid: string) => void
  clear: () => void
}

export function useDocumentUpload(): UseDocumentUploadResult {
  const [files, setFiles] = useState<UploadedFile[]>([])

  async function upload(file: File) {
    const uid = `${Date.now()}-${file.name}`
    const entry: UploadedFile = { uid, file, uploading: true }
    setFiles((prev) => [...prev, entry])

    try {
      const response = await uploadDocument(file)
      setFiles((prev) =>
        prev.map((f) => (f.uid === uid ? { ...f, response, uploading: false } : f)),
      )
    } catch (err) {
      const error =
        err instanceof Error ? err.message : typeof err === 'string' ? err : '上传失败'
      setFiles((prev) =>
        prev.map((f) => (f.uid === uid ? { ...f, error, uploading: false } : f)),
      )
    }
  }

  function remove(uid: string) {
    setFiles((prev) => prev.filter((f) => f.uid !== uid))
  }

  function clear() {
    setFiles([])
  }

  return { files, upload, remove, clear }
}

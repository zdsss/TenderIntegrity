import { createContext, useContext, useState } from 'react'
import { useDocumentUpload } from '../hooks/useDocumentUpload'
import type { UploadedFile } from '../hooks/useDocumentUpload'

interface UploadSession {
  files: UploadedFile[]
  upload: (file: File) => Promise<void>
  remove: (uid: string) => void
  clear: () => void
  taskId: string | null
  setTaskId: (id: string | null) => void
}

const UploadSessionContext = createContext<UploadSession | null>(null)

export function UploadSessionProvider({ children }: { children: React.ReactNode }) {
  const { files, upload, remove, clear } = useDocumentUpload()
  const [taskId, setTaskId] = useState<string | null>(null)

  return (
    <UploadSessionContext.Provider value={{ files, upload, remove, clear, taskId, setTaskId }}>
      {children}
    </UploadSessionContext.Provider>
  )
}

export function useUploadSession(): UploadSession {
  const ctx = useContext(UploadSessionContext)
  if (!ctx) throw new Error('useUploadSession must be used within UploadSessionProvider')
  return ctx
}

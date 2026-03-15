import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import UploadPage from '../../../src/pages/UploadPage'
import { UploadSessionProvider } from '../../../src/context/UploadSessionContext'

vi.mock('../../../src/api/documents', () => ({
  uploadDocument: vi.fn(),
}))
vi.mock('../../../src/api/tasks', () => ({
  createTask: vi.fn(),
  getTask: vi.fn(),
}))

import { uploadDocument } from '../../../src/api/documents'
import { createTask, getTask } from '../../../src/api/tasks'
const mockUpload = vi.mocked(uploadDocument)
const mockCreate = vi.mocked(createTask)
const mockGetTask = vi.mocked(getTask)

function renderPage() {
  return render(
    <MemoryRouter>
      <UploadSessionProvider>
        <UploadPage />
      </UploadSessionProvider>
    </MemoryRouter>,
  )
}

function makeFile(name = 'tender.docx') {
  return new File(['content'], name, {
    type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  })
}

describe('UploadPage integration', () => {
  beforeEach(() => {
    mockUpload.mockReset()
    mockCreate.mockReset()
    mockGetTask.mockReset()
  })

  it('renders upload zone and start button is disabled initially', () => {
    renderPage()
    expect(screen.getByText('点击或拖拽文件到此区域上传')).toBeInTheDocument()
  })

  it('shows file list after successful upload', async () => {
    mockUpload.mockResolvedValue({
      doc_id: 'doc-111',
      filename: 'tender.docx',
      file_size: 1024,
      message: '上传成功',
    })

    renderPage()
    const input = document.querySelector('input[type="file"]')!
    await userEvent.upload(input, makeFile())

    await waitFor(() =>
      expect(screen.getByText('tender.docx')).toBeInTheDocument(),
    )
  })

  it('enables start button only when ≥2 files uploaded', async () => {
    mockUpload
      .mockResolvedValueOnce({ doc_id: 'a', filename: 'a.docx', file_size: 100, message: '上传成功' })
      .mockResolvedValueOnce({ doc_id: 'b', filename: 'b.docx', file_size: 100, message: '上传成功' })

    renderPage()
    const input = document.querySelector('input[type="file"]')!

    // Upload both files in one call (input has multiple=true)
    await userEvent.upload(input, [makeFile('a.docx'), makeFile('b.docx')])

    await waitFor(() => {
      expect(screen.getByText('a.docx')).toBeInTheDocument()
      expect(screen.getByText('b.docx')).toBeInTheDocument()
    }, { timeout: 3000 })

    const startBtn = screen.getByRole('button', { name: '开始检测' })
    expect(startBtn).not.toBeDisabled()
  })

  it('creates task on start and shows progress', async () => {
    mockUpload
      .mockResolvedValueOnce({ doc_id: 'a', filename: 'a.docx', file_size: 100, message: '上传成功' })
      .mockResolvedValueOnce({ doc_id: 'b', filename: 'b.docx', file_size: 100, message: '上传成功' })
    mockCreate.mockResolvedValue({ task_id: 'task-1', status: 'pending', progress: 0 })
    mockGetTask.mockResolvedValue({ task_id: 'task-1', status: 'running', progress: 0.3 })

    renderPage()
    const input = document.querySelector('input[type="file"]')!

    await userEvent.upload(input, [makeFile('a.docx'), makeFile('b.docx')])

    await waitFor(() => {
      expect(screen.getByText('a.docx')).toBeInTheDocument()
      expect(screen.getByText('b.docx')).toBeInTheDocument()
    }, { timeout: 3000 })

    await userEvent.click(screen.getByRole('button', { name: '开始检测' }))

    await waitFor(() => expect(mockCreate).toHaveBeenCalledWith({
      doc_ids: ['a', 'b'],
      comparison_mode: 'pairwise',
    }), { timeout: 3000 })

    await waitFor(() => expect(screen.getByText('检测中')).toBeInTheDocument(), {
      timeout: 3000,
    })
  })
})

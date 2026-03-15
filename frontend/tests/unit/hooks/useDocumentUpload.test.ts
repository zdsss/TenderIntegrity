import { renderHook, act, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { useDocumentUpload } from '../../../src/hooks/useDocumentUpload'

vi.mock('../../../src/api/documents', () => ({
  uploadDocument: vi.fn(),
}))

import { uploadDocument } from '../../../src/api/documents'
const mockUpload = vi.mocked(uploadDocument)

function makeFile(name = 'test.docx', size = 1024) {
  return new File(['x'.repeat(size)], name, {
    type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  })
}

describe('useDocumentUpload', () => {
  beforeEach(() => mockUpload.mockReset())

  it('starts with empty files list', () => {
    const { result } = renderHook(() => useDocumentUpload())
    expect(result.current.files).toHaveLength(0)
  })

  it('adds file entry and resolves with response', async () => {
    mockUpload.mockResolvedValue({
      doc_id: 'doc-1',
      filename: 'test.docx',
      file_size: 1024,
      message: '上传成功',
    })

    const { result } = renderHook(() => useDocumentUpload())
    const file = makeFile()

    await act(async () => {
      await result.current.upload(file)
    })

    expect(result.current.files).toHaveLength(1)
    expect(result.current.files[0].response?.doc_id).toBe('doc-1')
    expect(result.current.files[0].uploading).toBe(false)
  })

  it('supports multiple sequential uploads', async () => {
    mockUpload
      .mockResolvedValueOnce({ doc_id: 'a', filename: 'a.docx', file_size: 100, message: '上传成功' })
      .mockResolvedValueOnce({ doc_id: 'b', filename: 'b.docx', file_size: 200, message: '上传成功' })

    const { result } = renderHook(() => useDocumentUpload())

    await act(async () => {
      await result.current.upload(makeFile('a.docx'))
      await result.current.upload(makeFile('b.docx'))
    })

    expect(result.current.files).toHaveLength(2)
    expect(result.current.files[0].response?.doc_id).toBe('a')
    expect(result.current.files[1].response?.doc_id).toBe('b')
  })

  it('removes file by uid', async () => {
    mockUpload.mockResolvedValue({
      doc_id: 'doc-2',
      filename: 'a.docx',
      file_size: 512,
      message: '上传成功',
    })

    const { result } = renderHook(() => useDocumentUpload())

    await act(async () => {
      await result.current.upload(makeFile('a.docx'))
    })

    const uid = result.current.files[0].uid
    act(() => result.current.remove(uid))
    expect(result.current.files).toHaveLength(0)
  })

  it('clears all files', async () => {
    mockUpload.mockResolvedValue({
      doc_id: 'x',
      filename: 'x.docx',
      file_size: 1,
      message: '上传成功',
    })

    const { result } = renderHook(() => useDocumentUpload())

    await act(async () => {
      await result.current.upload(makeFile())
      await result.current.upload(makeFile('b.docx'))
    })

    act(() => result.current.clear())
    expect(result.current.files).toHaveLength(0)
  })
})

import { render, screen, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import ReportPage from '../../../src/pages/ReportPage'
import type { RiskReportResponse } from '../../../src/types/api'

vi.mock('../../../src/api/reports', () => ({
  getReport: vi.fn(),
  downloadFile: vi.fn(),
}))

import { getReport } from '../../../src/api/reports'
const mockGetReport = vi.mocked(getReport)

const MOCK_REPORT: RiskReportResponse = {
  task_id: 'task-xyz',
  overall_risk_level: 'medium',
  overall_similarity_rate: 0.55,
  risk_summary: { high: 0, medium: 2, low: 1 },
  risk_pairs: [
    {
      pair_id: 'pair-1',
      risk_level: 'medium',
      risk_type: 'semantic_paraphrase',
      final_score: 0.65,
      vector_similarity: 0.71,
      keyword_overlap: 0.48,
      doc_a: { filename: 'file_a.docx', section: '第一章', content: '采购内容A' },
      doc_b: { filename: 'file_b.docx', section: '第一章', content: '采购内容B' },
      reason_zh: '两份文件语义高度相似',
      suggest_action: '建议复核',
      confidence: 0.88,
    },
  ],
}

function renderReport(taskId = 'task-xyz') {
  return render(
    <MemoryRouter initialEntries={[`/tasks/${taskId}/report`]}>
      <Routes>
        <Route path="/tasks/:taskId/report" element={<ReportPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('ReportPage integration', () => {
  beforeEach(() => {
    mockGetReport.mockReset()
  })

  it('shows loading spinner initially', () => {
    mockGetReport.mockResolvedValue(MOCK_REPORT)
    renderReport()
    expect(document.querySelector('.ant-spin')).toBeInTheDocument()
  })

  it('renders report header after data loads', async () => {
    mockGetReport.mockResolvedValue(MOCK_REPORT)
    renderReport()
    // Wait for any '中风险' badge to appear (header or table)
    await waitFor(() => expect(screen.getAllByText('中风险').length).toBeGreaterThan(0), {
      timeout: 3000,
    })
    // Ant Design Statistic splits int/decimal; check via DOM
    const valueEl = document.querySelector('.ant-statistic-content-value')
    expect(valueEl?.textContent).toContain('55.0')
  })

  it('renders risk pair rows', async () => {
    mockGetReport.mockResolvedValue(MOCK_REPORT)
    renderReport()
    await waitFor(() => expect(screen.getByText('语义改写')).toBeInTheDocument(), {
      timeout: 3000,
    })
  })

  it('shows error when report load fails', async () => {
    mockGetReport.mockRejectedValue({ message: '报告不存在' })
    renderReport()
    await waitFor(() => expect(screen.getByText('加载失败')).toBeInTheDocument(), {
      timeout: 3000,
    })
  })
})

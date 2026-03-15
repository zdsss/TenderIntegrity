import { render, screen } from '@testing-library/react'
import ReportHeader from '../../../src/pages/ReportPage/ReportHeader'
import type { RiskReportResponse } from '../../../src/types/api'

vi.mock('../../../src/api/reports', () => ({
  downloadFile: vi.fn(),
}))

const MOCK_REPORT: RiskReportResponse = {
  task_id: 'task-abc',
  overall_risk_level: 'high',
  overall_similarity_rate: 0.72,
  risk_summary: { high: 3, medium: 1, low: 2 },
  risk_pairs: [],
}

describe('ReportHeader', () => {
  it('displays overall risk level badge', () => {
    render(<ReportHeader report={MOCK_REPORT} />)
    expect(screen.getByText('高风险')).toBeInTheDocument()
  })

  it('displays similarity rate', () => {
    render(<ReportHeader report={MOCK_REPORT} />)
    // Ant Design Statistic splits integer / decimal into separate spans;
    // use the parent content-value element.
    const valueEl = document.querySelector('.ant-statistic-content-value')
    expect(valueEl?.textContent).toContain('72.0')
  })

  it('displays risk summary counts', () => {
    render(<ReportHeader report={MOCK_REPORT} />)
    expect(screen.getByText('3')).toBeInTheDocument() // high
    expect(screen.getByText('1')).toBeInTheDocument() // medium
    expect(screen.getByText('2')).toBeInTheDocument() // low
  })

  it('renders export buttons', () => {
    render(<ReportHeader report={MOCK_REPORT} />)
    expect(screen.getByRole('button', { name: /导出 CSV/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /导出 PDF/ })).toBeInTheDocument()
  })
})

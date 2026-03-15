import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import TaskTable from '../../../src/pages/TaskHistoryPage/TaskTable'
import type { TaskResponse } from '../../../src/types/api'

const TASKS: TaskResponse[] = [
  {
    task_id: 'task-aaa-111',
    status: 'done',
    progress: 1,
    overall_risk_level: 'high',
    overall_similarity_rate: 0.85,
    created_at: '2024-03-01T10:00:00Z',
  },
  {
    task_id: 'task-bbb-222',
    status: 'running',
    progress: 0.5,
    overall_risk_level: null,
    overall_similarity_rate: null,
    created_at: '2024-03-02T12:00:00Z',
  },
]

function renderTable(overrides: Partial<React.ComponentProps<typeof TaskTable>> = {}) {
  const defaults = {
    tasks: TASKS,
    loading: false,
    total: 2,
    page: 1,
    pageSize: 10,
    onPageChange: vi.fn(),
    onDelete: vi.fn().mockResolvedValue(undefined),
  }
  return render(
    <MemoryRouter>
      <TaskTable {...defaults} {...overrides} />
    </MemoryRouter>,
  )
}

describe('TaskTable', () => {
  it('renders task rows', () => {
    renderTable()
    expect(screen.getByText(/task-aaa/)).toBeInTheDocument()
    expect(screen.getByText(/task-bbb/)).toBeInTheDocument()
  })

  it('shows 高风险 badge for high risk level', () => {
    renderTable()
    expect(screen.getByText('高风险')).toBeInTheDocument()
  })

  it('shows — for null risk level', () => {
    renderTable()
    const dashes = screen.getAllByText('—')
    expect(dashes.length).toBeGreaterThanOrEqual(1)
  })

  it('shows similarity rate as percentage', () => {
    renderTable()
    expect(screen.getByText('85.0%')).toBeInTheDocument()
  })

  it('"查看报告" button disabled for non-done tasks', () => {
    renderTable()
    const reportButtons = screen.getAllByRole('button', { name: '查看报告' })
    const runningTaskBtn = reportButtons.find((btn) => btn.closest('tr')?.textContent?.includes('task-bbb'))
    expect(runningTaskBtn).toBeDisabled()
  })

  it('"查看报告" button enabled for done tasks', () => {
    renderTable()
    const reportButtons = screen.getAllByRole('button', { name: '查看报告' })
    const doneTaskBtn = reportButtons.find((btn) => btn.closest('tr')?.textContent?.includes('task-aaa'))
    expect(doneTaskBtn).not.toBeDisabled()
  })

  it('renders delete buttons for each task', () => {
    renderTable()
    const deleteButtons = screen.getAllByRole('button', { name: '删除' })
    expect(deleteButtons).toHaveLength(TASKS.length)
  })

  it('shows loading state', () => {
    renderTable({ loading: true })
    // Ant Design Table shows a loading overlay
    const loadingEl = document.querySelector('.ant-spin')
    expect(loadingEl).toBeInTheDocument()
  })
})

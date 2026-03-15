import { render, screen } from '@testing-library/react'
import StatusBadge from '../../../src/components/StatusBadge'

describe('StatusBadge', () => {
  it('renders 排队中 for pending', () => {
    render(<StatusBadge status="pending" />)
    expect(screen.getByText('排队中')).toBeInTheDocument()
  })

  it('renders 检测中 for running', () => {
    render(<StatusBadge status="running" />)
    expect(screen.getByText('检测中')).toBeInTheDocument()
  })

  it('renders 已完成 for done', () => {
    render(<StatusBadge status="done" />)
    expect(screen.getByText('已完成')).toBeInTheDocument()
  })

  it('renders 失败 for error', () => {
    render(<StatusBadge status="error" />)
    expect(screen.getByText('失败')).toBeInTheDocument()
  })
})

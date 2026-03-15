import { render, screen } from '@testing-library/react'
import RiskBadge from '../../../src/components/RiskBadge'

describe('RiskBadge', () => {
  it('renders 高风险 for high', () => {
    render(<RiskBadge level="high" />)
    expect(screen.getByText('高风险')).toBeInTheDocument()
  })

  it('renders 中风险 for medium', () => {
    render(<RiskBadge level="medium" />)
    expect(screen.getByText('中风险')).toBeInTheDocument()
  })

  it('renders 低风险 for low', () => {
    render(<RiskBadge level="low" />)
    expect(screen.getByText('低风险')).toBeInTheDocument()
  })

  it('renders 无风险 for none', () => {
    render(<RiskBadge level="none" />)
    expect(screen.getByText('无风险')).toBeInTheDocument()
  })

  it('falls back to raw string for unknown level', () => {
    render(<RiskBadge level="unknown_xyz" />)
    expect(screen.getByText('unknown_xyz')).toBeInTheDocument()
  })
})

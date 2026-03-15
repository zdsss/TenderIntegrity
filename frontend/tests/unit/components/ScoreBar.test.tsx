import { render, screen } from '@testing-library/react'
import ScoreBar from '../../../src/components/ScoreBar'

describe('ScoreBar', () => {
  it('renders progress element', () => {
    render(<ScoreBar score={0.5} />)
    // Ant Design Progress renders an aria-valuenow attribute
    const progressBar = document.querySelector('[role="progressbar"]')
    expect(progressBar).toBeInTheDocument()
  })

  it('shows 50% for score=0.5', () => {
    render(<ScoreBar score={0.5} />)
    expect(screen.getByText('50%')).toBeInTheDocument()
  })

  it('shows success icon for score=1 (antd behavior)', () => {
    render(<ScoreBar score={1} />)
    const bar = document.querySelector('[role="progressbar"]')
    expect(bar).toHaveAttribute('aria-valuenow', '100')
  })

  it('shows 0% for score=0', () => {
    render(<ScoreBar score={0} />)
    expect(screen.getByText('0%')).toBeInTheDocument()
  })
})

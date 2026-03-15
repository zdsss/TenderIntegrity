import { Progress } from 'antd'

interface Props {
  score: number   // 0–1
  thresholdHigh?: number
  thresholdMedium?: number
}

export default function ScoreBar({
  score,
  thresholdHigh = 0.7,
  thresholdMedium = 0.4,
}: Props) {
  const pct = Math.round(score * 100)
  let strokeColor = '#52c41a'   // green — low
  if (score >= thresholdHigh) strokeColor = '#ff4d4f'        // red
  else if (score >= thresholdMedium) strokeColor = '#fa8c16' // orange

  return (
    <Progress
      percent={pct}
      strokeColor={strokeColor}
      size="small"
      style={{ minWidth: 120 }}
    />
  )
}

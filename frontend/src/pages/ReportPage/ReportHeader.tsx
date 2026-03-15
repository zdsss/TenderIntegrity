import { Card, Col, Row, Statistic, Typography } from 'antd'
import RiskBadge from '../../components/RiskBadge'
import ExportButtons from '../../components/ExportButtons'
import type { RiskReportResponse } from '../../types/api'

const { Title } = Typography

interface Props {
  report: RiskReportResponse
}

export default function ReportHeader({ report }: Props) {
  const { overall_risk_level, overall_similarity_rate, risk_summary, task_id } = report
  const summaryMap = risk_summary ?? {}

  return (
    <Card style={{ marginBottom: 24 }}>
      <Row gutter={[16, 16]} align="middle">
        <Col>
          <Title level={4} style={{ margin: 0 }}>
            总体风险等级：
          </Title>
        </Col>
        <Col>
          <RiskBadge level={overall_risk_level} />
        </Col>
        <Col flex="auto" />
        <Col>
          <ExportButtons taskId={task_id} />
        </Col>
      </Row>

      <Row gutter={[24, 16]} style={{ marginTop: 16 }}>
        <Col>
          <Statistic
            title="综合雷同率"
            value={(overall_similarity_rate * 100).toFixed(1)}
            suffix="%"
          />
        </Col>
        <Col>
          <Statistic title="高风险对" value={summaryMap.high ?? 0} styles={{ content: { color: '#ff4d4f' } }} />
        </Col>
        <Col>
          <Statistic title="中风险对" value={summaryMap.medium ?? 0} styles={{ content: { color: '#fa8c16' } }} />
        </Col>
        <Col>
          <Statistic title="低风险对" value={summaryMap.low ?? 0} styles={{ content: { color: '#1677ff' } }} />
        </Col>
      </Row>
    </Card>
  )
}

import { Alert, Badge, Card, Col, Row, Space, Tag, Typography } from 'antd'
import type { CompositeRisk, MetaComparison, PriceAnalysis, RareTokenAnalysis } from '../../types/api'

const { Text, Title } = Typography

interface Props {
  compositeRisk?: CompositeRisk | null
  rareTokenAnalysis?: RareTokenAnalysis | null
  priceAnalysis?: PriceAnalysis | null
  metaComparison?: MetaComparison | null
}

function riskColor(level: string): string {
  if (level === 'high') return '#ff4d4f'
  if (level === 'medium') return '#fa8c16'
  if (level === 'low') return '#1677ff'
  return '#8c8c8c'
}

function riskTag(level: string) {
  const color =
    level === 'high' ? 'error' : level === 'medium' ? 'warning' : level === 'low' ? 'processing' : 'default'
  const label =
    level === 'high' ? '高风险' : level === 'medium' ? '中风险' : level === 'low' ? '低风险' : '无风险'
  return <Tag color={color}>{label}</Tag>
}

export default function RiskSynthesisPanel({
  compositeRisk,
  rareTokenAnalysis,
  priceAnalysis,
  metaComparison,
}: Props) {
  const hasAnyData = compositeRisk || rareTokenAnalysis || priceAnalysis || metaComparison
  if (!hasAnyData) return null

  const signals = compositeRisk?.triggered_signals ?? []

  return (
    <Card
      title={
        <Space>
          <Title level={5} style={{ margin: 0 }}>
            综合风险信号分析
          </Title>
          {compositeRisk && (
            <Badge
              count={signals.length}
              style={{ backgroundColor: signals.length > 0 ? '#ff4d4f' : '#8c8c8c' }}
              showZero
            />
          )}
        </Space>
      }
      style={{ marginBottom: 24 }}
    >
      {/* Triggered signals */}
      {signals.length > 0 && (
        <Alert
          type="error"
          showIcon
          message={`检测到 ${signals.length} 项高风险信号（已触发综合风险升级）`}
          description={
            <ul style={{ margin: '8px 0 0', paddingLeft: 20 }}>
              {signals.map((sig, i) => (
                <li key={i} style={{ marginBottom: 4 }}>
                  {sig}
                </li>
              ))}
            </ul>
          }
          style={{ marginBottom: 16 }}
        />
      )}

      <Row gutter={[16, 16]}>
        {/* Rare token analysis */}
        {rareTokenAnalysis && (
          <Col xs={24} md={8}>
            <Card
              size="small"
              title={
                <Space>
                  <span>罕见序列共现</span>
                  {riskTag(rareTokenAnalysis.risk_level)}
                </Space>
              }
            >
              <Text>
                共现序列数：
                <Text strong style={{ color: riskColor(rareTokenAnalysis.risk_level) }}>
                  {rareTokenAnalysis.total_match_count}
                </Text>
              </Text>
              {rareTokenAnalysis.number_unit_matches.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    量化参数复用：
                  </Text>
                  <div>
                    {rareTokenAnalysis.number_unit_matches.slice(0, 5).map((m, i) => (
                      <Tag key={i} style={{ marginBottom: 4 }}>
                        {m}
                      </Tag>
                    ))}
                    {rareTokenAnalysis.number_unit_matches.length > 5 && (
                      <Text type="secondary">+{rareTokenAnalysis.number_unit_matches.length - 5} 项</Text>
                    )}
                  </div>
                </div>
              )}
            </Card>
          </Col>
        )}

        {/* Price analysis */}
        {priceAnalysis && (
          <Col xs={24} md={8}>
            <Card
              size="small"
              title={
                <Space>
                  <span>价格协同检测</span>
                  {riskTag(priceAnalysis.risk_level)}
                </Space>
              }
            >
              {priceAnalysis.proximity_ratio != null ? (
                <>
                  <Text>
                    报价接近度：
                    <Text strong style={{ color: riskColor(priceAnalysis.risk_level) }}>
                      {(priceAnalysis.proximity_ratio * 100).toFixed(2)}%
                    </Text>
                  </Text>
                  <div style={{ marginTop: 4 }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      A: {priceAnalysis.total_a != null ? `¥${priceAnalysis.total_a.toLocaleString()}` : '-'} &nbsp;|&nbsp;
                      B: {priceAnalysis.total_b != null ? `¥${priceAnalysis.total_b.toLocaleString()}` : '-'}
                    </Text>
                  </div>
                </>
              ) : (
                <Text type="secondary">未提取到有效报价数据</Text>
              )}
            </Card>
          </Col>
        )}

        {/* Meta comparison */}
        {metaComparison && (
          <Col xs={24} md={8}>
            <Card
              size="small"
              title={
                <Space>
                  <span>文档元数据对比</span>
                  {riskTag(metaComparison.risk_level)}
                </Space>
              }
            >
              {metaComparison.risk_notes.length > 0 ? (
                <ul style={{ margin: 0, paddingLeft: 16 }}>
                  {metaComparison.risk_notes.map((note, i) => (
                    <li key={i} style={{ fontSize: 12, marginBottom: 2 }}>
                      {note}
                    </li>
                  ))}
                </ul>
              ) : (
                <Text type="secondary">无异常元数据信号</Text>
              )}
            </Card>
          </Col>
        )}
      </Row>
    </Card>
  )
}

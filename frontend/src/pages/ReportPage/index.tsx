import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Alert, Card, Spin } from 'antd'
import { getReport } from '../../api/reports'
import type { RiskReportResponse } from '../../types/api'
import ReportHeader from './ReportHeader'
import RiskPairsTable from './RiskPairsTable'
import FieldOverlapAlert from './FieldOverlapAlert'
import RiskSynthesisPanel from './RiskSynthesisPanel'

export default function ReportPage() {
  const { taskId } = useParams<{ taskId: string }>()
  const [report, setReport] = useState<RiskReportResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!taskId) return
    setLoading(true)
    getReport(taskId)
      .then(setReport)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : '加载报告失败'),
      )
      .finally(() => setLoading(false))
  }, [taskId])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 64 }}>
        <Spin size="large" description="加载报告中…" />
      </div>
    )
  }

  if (error) {
    return <Alert type="error" title="加载失败" description={error} showIcon />
  }

  if (!report) {
    return <Alert type="warning" title="报告不存在" showIcon />
  }

  return (
    <div>
      <ReportHeader report={report} />
      <RiskSynthesisPanel
        compositeRisk={report.composite_risk}
        rareTokenAnalysis={report.rare_token_analysis}
        priceAnalysis={report.price_analysis}
        metaComparison={report.meta_comparison}
      />
      <FieldOverlapAlert overlaps={report.field_overlaps ?? []} />
      <Card title={`风险对列表（共 ${report.risk_pairs.length} 对）`}>
        <RiskPairsTable pairs={report.risk_pairs} />
      </Card>
    </div>
  )
}

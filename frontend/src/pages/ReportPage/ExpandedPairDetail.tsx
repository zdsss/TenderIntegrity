import { Col, Descriptions, Row, Typography } from 'antd'
import type { RiskPairDetail } from '../../types/api'

const { Text, Paragraph } = Typography

interface Props {
  pair: RiskPairDetail
}

function DocSection({ doc, label }: { doc: RiskPairDetail['doc_a']; label: string }) {
  return (
    <Col span={12}>
      <Descriptions
        title={label}
        size="small"
        column={1}
        bordered
        items={[
          { key: 'filename', label: '文件名', children: doc.filename ?? '—' },
          { key: 'section', label: '章节', children: doc.section ?? '—' },
          {
            key: 'content',
            label: '内容',
            children: (
              <Paragraph
                ellipsis={{ rows: 4, expandable: true }}
                style={{ margin: 0 }}
              >
                {String(doc.content ?? '')}
              </Paragraph>
            ),
          },
        ]}
      />
    </Col>
  )
}

export default function ExpandedPairDetail({ pair }: Props) {
  return (
    <div style={{ padding: '12px 16px' }}>
      <Row gutter={[16, 16]}>
        <DocSection doc={pair.doc_a} label="文档 A" />
        <DocSection doc={pair.doc_b} label="文档 B" />
      </Row>
      <Row gutter={[16, 16]} style={{ marginTop: 12 }}>
        <Col span={24}>
          <Text strong>AI 分析：</Text>
          <Paragraph style={{ margin: '4px 0 0' }}>{pair.reason_zh}</Paragraph>
        </Col>
        <Col span={24}>
          <Text strong>建议操作：</Text>
          <Paragraph style={{ margin: '4px 0 0' }}>{pair.suggest_action}</Paragraph>
        </Col>
      </Row>
    </div>
  )
}

/** All API request / response types, mirroring the backend Pydantic schemas. */

// ── Documents ──────────────────────────────────────────────────────────────

export interface DocumentUploadResponse {
  doc_id: string
  filename: string
  file_size: number
  message: string
}

// ── Tasks ──────────────────────────────────────────────────────────────────

export type ComparisonMode = 'pairwise' | 'all_vs_all'

export interface TaskCreateRequest {
  doc_ids: string[]
  comparison_mode: ComparisonMode
}

/** Backend statuses: pending | running | done | error */
export type TaskStatus = 'pending' | 'running' | 'done' | 'error'

export interface TaskResponse {
  task_id: string
  status: TaskStatus
  progress: number
  overall_risk_level?: string | null
  overall_similarity_rate?: number | null
  error_message?: string | null
  created_at?: string | null
}

// ── Reports ────────────────────────────────────────────────────────────────

export type RiskLevel = 'high' | 'medium' | 'low' | 'none'

export interface DocSection {
  doc_id?: string
  filename?: string
  section?: string
  content?: string
  [key: string]: unknown
}

export interface RiskPairDetail {
  pair_id: string
  risk_level: RiskLevel
  risk_type: string
  final_score: number
  vector_similarity: number
  keyword_overlap: number
  doc_a: DocSection
  doc_b: DocSection
  reason_zh: string
  suggest_action: string
  confidence: number
}

export interface RiskSummary {
  high_count?: number
  medium_count?: number
  low_count?: number
  total_count?: number
  [key: string]: number | undefined
}

export interface StructureAnalysis {
  title_jaccard: number
  sequence_similarity: number
  matched_sections: [string, string][]
  structure_risk_level: RiskLevel | 'none'
  overall_score: number
}

export interface FieldOverlap {
  field_type: 'phone' | 'email' | 'person' | 'company' | 'project' | 'team_member'
  value_a: string
  value_b: string
  overlap_type: 'exact' | 'fuzzy'
  risk_note: string
}

export interface RareTokenMatch {
  token: string
  freq_in_a: number
  freq_in_b: number
  token_type: '4gram' | 'number_unit'
  risk_note: string
}

export interface RareTokenAnalysis {
  matches: RareTokenMatch[]
  risk_level: RiskLevel | 'none'
  total_match_count: number
  number_unit_matches: string[]
}

export interface PriceAnalysis {
  risk_level: RiskLevel | 'none'
  total_a: number | null
  total_b: number | null
  proximity_ratio: number | null
  is_price_coordinated: boolean
  coordinated_evidence: string[]
}

export interface MetaComparison {
  risk_level: RiskLevel | 'none'
  same_author: boolean
  same_last_modifier: boolean
  same_company: boolean
  time_gap_minutes: number | null
  is_timestamp_clustered: boolean
  risk_notes: string[]
}

export interface CompositeRisk {
  final_level: RiskLevel
  text_risk_level: RiskLevel
  triggered_signals: string[]
  signal_breakdown: Record<string, unknown>
}

export interface RiskReportResponse {
  task_id: string
  overall_risk_level: RiskLevel
  overall_similarity_rate: number
  risk_summary: RiskSummary
  risk_pairs: RiskPairDetail[]
  structure_analysis?: StructureAnalysis | null
  field_overlaps?: FieldOverlap[]
  rare_token_analysis?: RareTokenAnalysis | null
  price_analysis?: PriceAnalysis | null
  meta_comparison?: MetaComparison | null
  composite_risk?: CompositeRisk | null
}

export interface Commodity {
  id: string
  name_es: string
  name_en: string
  unit: string
  category: string
  description: string
}

export interface Price {
  id: number
  commodity_id: string
  date: string
  price: number
  source: string
  price_type: string
  currency: string
}

export interface Company {
  id: number
  commodity_id: string
  name: string
  ticker: string | null
  exchange: string | null
  country: string
  province_ar: string | null
  project_name: string | null
  role: string
  is_ar_actor: number
  notes: string
}

export interface NewsItem {
  id: number
  commodity_id: string | null
  commodity_name: string | null
  title: string
  snippet: string | null
  url: string
  source: string
  published_at: string | null
  sentiment: 'positive' | 'negative' | 'neutral' | null
  signal_type: string | null
  relevance_score: number | null
  summary_es: string | null
  impact_direction: 'bullish' | 'bearish' | 'neutral' | null
  llm_provider: string | null
}

export interface TradeFlow {
  commodity_id: string
  ncm: string
  period: string        // '2024-01'
  flow_type: 'export' | 'import'
  value_usd: number | null
  weight_kg: number | null
  source: string
}

export interface TradeSummary {
  commodity_id: string
  total_export_usd: number
  from_period: string
  to_period: string
  data_points: number
}

export interface WeeklySummary {
  id: number
  commodity_id: string
  generated_at: string
  period_start: string
  period_end: string
  summary_text: string
  key_signals: string[]
  llm_provider: string | null
}

export interface Alert {
  id: number
  commodity_id: string
  commodity_name: string | null
  generated_at: string
  title: string
  description: string | null
  severity: 'high' | 'medium'
  signal_type: string | null
  llm_provider: string | null
  is_active: number
  expires_at: string | null
}

export interface TradePartner {
  country: string
  commodity_id: string
  total_usd: number
  year: number
  flow_type: string
}

export interface ImpactVariable {
  id: number
  commodity_id: string | null
  variable_name: string
  date: string
  value: number | null
  value_text: string | null
  source: string
  unit: string | null
  prev_value?: number | null   // valor del período anterior (para calcular tendencia)
  prev_date?: string | null
}

export interface Valuation {
  id: number
  company_id: number
  date: string
  close_price: number | null
  open_price: number | null
  high_price: number | null
  low_price: number | null
  volume: number | null
  market_cap_usd: number | null
  pe_ratio: number | null
  ev_ebitda: number | null
  currency: string
  source: string
  name: string
  ticker: string
  commodity_id: string
}

export interface CorrelationEntry {
  c1: string
  c2: string
  r: number | null
  n: number
}

export interface CorrelationMatrix {
  window: number
  commodities: string[]
  matrix: CorrelationEntry[]
}

export type RegimeLabel = 'ALCISTA' | 'BAJISTA' | 'LATERAL' | 'VOLÁTIL'

export interface MarketRegime {
  commodity_id: string
  regime: RegimeLabel
  current_price: number
  sma20: number | null
  sma50: number | null
  sma200: number | null
  boll_upper: number | null
  boll_lower: number | null
  n_days: number
}

export interface PipelineStatus {
  pipeline_name: string
  description: string
  last_run: string | null
  status: 'success' | 'error' | 'running' | 'never_run'
  records_processed: number
  records_skipped: number
  error_message: string | null
  finished_at: string | null
}

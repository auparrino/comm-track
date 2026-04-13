// En desarrollo: proxy vite → localhost:8000
// En producción: VITE_API_URL=https://comm-track-backend.fly.dev
const BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}`
  : '/api'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

async function post<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: 'POST' })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export const api = {
  commodities: {
    list: () => get<import('../types').Commodity[]>('/commodities/'),
    get: (id: string) => get<import('../types').Commodity>(`/commodities/${id}`),
  },
  prices: {
    latest: (commodityId: string) => get<import('../types').Price>(`/prices/${commodityId}/latest`),
    history: (commodityId: string, days = 90, priceType?: string) =>
      get<import('../types').Price[]>(
        `/prices/${commodityId}?days=${days}${priceType ? `&price_type=${priceType}` : ''}`
      ),
    correlations: (window = 90) =>
      get<import('../types').CorrelationMatrix>(`/prices/correlations?window=${window}`),
    regime: (commodityId: string) =>
      get<import('../types').MarketRegime>(`/prices/${commodityId}/regime`),
    signals: (commodityId: string) =>
      get<import('../types').SignalsResult>(`/prices/${commodityId}/signals`),
  },
  news: {
    list: (params: { commodity?: string; days?: number; sentiment?: string; signal?: string; limit?: number } = {}) => {
      const q = new URLSearchParams()
      if (params.commodity) q.set('commodity', params.commodity)
      if (params.days)      q.set('days', String(params.days))
      if (params.sentiment) q.set('sentiment', params.sentiment)
      if (params.signal)    q.set('signal', params.signal)
      if (params.limit)     q.set('limit', String(params.limit))
      return get<import('../types').NewsItem[]>(`/news/?${q}`)
    },
  },
  trade: {
    flows: (params: { commodity?: string; months?: number; ncm?: string } = {}) => {
      const q = new URLSearchParams()
      if (params.commodity) q.set('commodity', params.commodity)
      if (params.months)    q.set('months', String(params.months))
      if (params.ncm)       q.set('ncm', params.ncm)
      return get<import('../types').TradeFlow[]>(`/trade-flows/?${q}`)
    },
    summary: (params: { commodity?: string; months?: number } = {}) => {
      const q = new URLSearchParams()
      if (params.commodity) q.set('commodity', params.commodity)
      if (params.months)    q.set('months', String(params.months))
      return get<import('../types').TradeSummary[]>(`/trade-flows/summary?${q}`)
    },
  },
  variables: {
    latest: (commodity?: string) => {
      const q = new URLSearchParams()
      if (commodity) q.set('commodity', commodity)
      return get<import('../types').ImpactVariable[]>(`/impact-variables/latest?${q}`)
    },
    history: (variable: string, days = 180, commodity?: string) => {
      const q = new URLSearchParams()
      q.set('variable', variable)
      q.set('days', String(days))
      if (commodity) q.set('commodity', commodity)
      return get<import('../types').ImpactVariable[]>(`/impact-variables/?${q}`)
    },
  },
  summary: {
    get: (commodityId: string) =>
      get<import('../types').WeeklySummary>(`/summary/${commodityId}`),
    list: (commodity?: string) => {
      const q = new URLSearchParams()
      if (commodity) q.set('commodity', commodity)
      return get<import('../types').WeeklySummary[]>(`/summary/?${q}`)
    },
  },
  alerts: {
    list: (commodity?: string, activeOnly = true) => {
      const q = new URLSearchParams()
      if (commodity) q.set('commodity', commodity)
      q.set('active_only', String(activeOnly))
      return get<import('../types').Alert[]>(`/alerts/?${q}`)
    },
  },
  trade_partners: {
    list: (params: { commodity?: string; year?: number; flow?: string; top?: number } = {}) => {
      const q = new URLSearchParams()
      if (params.commodity) q.set('commodity', params.commodity)
      if (params.year)      q.set('year', String(params.year))
      if (params.flow)      q.set('flow', params.flow)
      if (params.top)       q.set('top', String(params.top))
      return get<import('../types').TradePartner[]>(`/trade-flows/partners?${q}`)
    },
  },
  companies: {
    list: (commodity?: string) =>
      get<import('../types').Company[]>(
        commodity ? `/companies/?commodity=${commodity}` : '/companies/'
      ),
    valuations: (companyId: number, days = 90) =>
      get<import('../types').Valuation[]>(`/companies/${companyId}/valuations?days=${days}`),
  },
  admin: {
    pipelines: () => get<import('../types').PipelineStatus[]>('/admin/pipelines'),
    run: (name: string) => post<{ status: string; pipeline: string }>(`/admin/pipelines/${name}/run`),
  },
}

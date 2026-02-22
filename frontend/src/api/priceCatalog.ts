import request from './request'

export interface PriceCatalogItem {
  id: string
  country: string | null
  name: string
  cert_type: string | null
  sample_qty: number | null
  based_on_report: string | null
  lead_weeks: number | null
  includes_testing: string | null
  cert_validity_years: number | null
  series_apply: string | null
  ref_price: number | null
  remark: string | null
  created_at: string
  updated_at: string
}

export interface PriceCatalogSearchItem {
  id: string
  country: string | null
  name: string
  based_on_report: string | null
  lead_weeks: number | null
  includes_testing: string | null
  series_apply: string | null
  ref_price: number | null
}

export const priceCatalogApi = {
  list(params: { page?: number; page_size?: number; keyword?: string }) {
    return request.get<any, { code: number; data: PriceCatalogItem[]; total: number }>('/price-catalog', { params })
  },
  search(params: { keyword?: string; country?: string }) {
    return request.get<any, { code: number; data: PriceCatalogSearchItem[] }>('/price-catalog/search', { params })
  },
  countries() {
    return request.get<any, { code: number; data: string[] }>('/price-catalog/countries')
  },
  create(data: Record<string, unknown>) {
    return request.post<any, { code: number; data: PriceCatalogItem }>('/price-catalog', data)
  },
  update(id: string, data: Record<string, unknown>) {
    return request.put<any, { code: number; data: PriceCatalogItem }>(`/price-catalog/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/price-catalog/${id}`)
  },
}

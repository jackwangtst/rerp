import request from './request'

export interface QuotationItem {
  country: string | null
  name: string
  standard: string | null
  lr_or_not: string | null
  weeks: number | null
  local_testing: string | null
  models: string | null
  unit_price: number
  discount: number
  amount: number
  item_remark: string | null
}

export interface QuotationListItem {
  id: string
  quote_no: string
  opp_id: string | null
  customer_id: string | null
  version: number
  total_amount: number
  discount_amount: number | null
  discount_rate: number | null
  valid_until: string
  status: string
  created_by: string | null
  created_at: string
}

export interface QuotationDetail extends QuotationListItem {
  items: QuotationItem[]
  contact_name: string | null
  contact_phone: string | null
  deliver_to_address: string | null
  payment_terms: string | null
  remark: string | null
  approved_by: string | null
  updated_at: string
}

export const quotationApi = {
  list(params: { page?: number; page_size?: number; status?: string; opp_id?: string }) {
    return request.get<any, { code: number; data: QuotationListItem[]; total: number }>('/quotations', { params })
  },
  get(id: string) {
    return request.get<any, { code: number; data: QuotationDetail }>(`/quotations/${id}`)
  },
  create(data: Record<string, unknown>) {
    return request.post<any, { code: number; data: QuotationDetail }>('/quotations', data)
  },
  update(id: string, data: Record<string, unknown>) {
    return request.put<any, { code: number; data: QuotationDetail }>(`/quotations/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/quotations/${id}`)
  },
}

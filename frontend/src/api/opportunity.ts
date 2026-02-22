import request from './request'

export interface OppListItem {
  id: string
  opp_name: string
  company_name: string
  stage: string
  certification_type: string
  estimated_amount: number | null
  expected_close_date: string | null
  win_probability: number | null
  assigned_to: string
  lead_id: string | null
  customer_id: string | null
  created_at: string
}

export interface OppDetail extends OppListItem {
  competitor: string | null
  loss_reason: string | null
  updated_at: string
  created_by: string | null
}

export interface OppFollowUp {
  id: string
  opp_id: string
  follow_type: string
  content: string
  next_date: string | null
  created_by: string | null
  created_at: string
}

export const oppApi = {
  list(params: { page?: number; page_size?: number; stage?: string; keyword?: string }) {
    return request.get<any, { code: number; data: OppListItem[]; total: number }>('/opportunities', { params })
  },
  get(id: string) {
    return request.get<any, { code: number; data: OppDetail }>(`/opportunities/${id}`)
  },
  create(data: Record<string, unknown>) {
    return request.post<any, { code: number; data: OppDetail }>('/opportunities', data)
  },
  update(id: string, data: Record<string, unknown>) {
    return request.put<any, { code: number; data: OppDetail }>(`/opportunities/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/opportunities/${id}`)
  },
  listFollowUps(oppId: string) {
    return request.get<any, { code: number; data: OppFollowUp[] }>(`/opportunities/${oppId}/follow-ups`)
  },
  addFollowUp(oppId: string, data: Record<string, unknown>) {
    return request.post(`/opportunities/${oppId}/follow-ups`, data)
  },
}

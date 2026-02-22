import request from './request'

export interface LeadListItem {
  id: string
  company_name: string
  contact_name: string | null
  contact_phone: string
  source: string
  industry: string | null
  province: string | null
  city: string | null
  certification_interest: string | null
  status: string
  assigned_to: string | null
  next_follow_up_date: string | null
  created_at: string
}

export interface LeadDetail extends LeadListItem {
  contact_email: string | null
  remark: string | null
  updated_at: string
  created_by: string | null
}

export interface LeadFollowUp {
  id: string
  lead_id: string
  follow_type: string
  content: string
  next_date: string | null
  created_by: string | null
  created_at: string
}

export const leadApi = {
  list(params: { page?: number; page_size?: number; status?: string; keyword?: string }) {
    return request.get<any, { code: number; data: LeadListItem[]; total: number }>('/leads', { params })
  },
  get(id: string) {
    return request.get<any, { code: number; data: LeadDetail }>(`/leads/${id}`)
  },
  create(data: Record<string, unknown>) {
    return request.post<any, { code: number; data: LeadDetail }>('/leads', data)
  },
  update(id: string, data: Record<string, unknown>) {
    return request.put<any, { code: number; data: LeadDetail }>(`/leads/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/leads/${id}`)
  },
  listFollowUps(leadId: string) {
    return request.get<any, { code: number; data: LeadFollowUp[] }>(`/leads/${leadId}/follow-ups`)
  },
  addFollowUp(leadId: string, data: Record<string, unknown>) {
    return request.post(`/leads/${leadId}/follow-ups`, data)
  },
}

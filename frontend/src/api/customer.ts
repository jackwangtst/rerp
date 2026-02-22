import request from './request'

export interface CustomerListItem {
  id: string
  customer_no: string
  company_name: string
  company_short_name: string | null
  industry: string | null
  company_size: string | null
  province: string | null
  city: string | null
  customer_level: string | null
  status: string
  assigned_sales: string | null
  created_at: string
}

export interface Contact {
  id: string
  customer_id: string
  name: string
  title: string | null
  department: string | null
  phone: string
  email: string | null
  wechat: string | null
  is_primary: boolean
  created_at: string
}

export interface CustomerDetail extends CustomerListItem {
  unified_social_credit_code: string | null
  legal_representative: string | null
  address: string | null
  remark: string | null
  contacts: Contact[]
}

export interface FollowUp {
  id: string
  customer_id: string
  follow_type: string
  content: string
  next_date: string | null
  created_by: string | null
  created_at: string
}

export const customerApi = {
  list(params: { page?: number; page_size?: number; status?: string; keyword?: string }) {
    return request.get<any, { code: number; data: CustomerListItem[]; total: number }>('/customers', { params })
  },
  get(id: string) {
    return request.get<any, { code: number; data: CustomerDetail }>(`/customers/${id}`)
  },
  create(data: Record<string, unknown>) {
    return request.post<any, { code: number; data: CustomerDetail }>('/customers', data)
  },
  update(id: string, data: Record<string, unknown>) {
    return request.put<any, { code: number; data: CustomerDetail }>(`/customers/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/customers/${id}`)
  },
  addContact(customerId: string, data: Record<string, unknown>) {
    return request.post(`/customers/${customerId}/contacts`, data)
  },
  updateContact(customerId: string, contactId: string, data: Record<string, unknown>) {
    return request.put(`/customers/${customerId}/contacts/${contactId}`, data)
  },
  deleteContact(customerId: string, contactId: string) {
    return request.delete(`/customers/${customerId}/contacts/${contactId}`)
  },
  listFollowUps(customerId: string) {
    return request.get<any, { code: number; data: FollowUp[] }>(`/customers/${customerId}/follow-ups`)
  },
  addFollowUp(customerId: string, data: Record<string, unknown>) {
    return request.post(`/customers/${customerId}/follow-ups`, data)
  },
}

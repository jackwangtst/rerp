import request from './request'

export interface ContractItem {
  id: string
  contract_id: string
  item_name: string
  standard: string | null
  audit_days: number | null
  unit_price: number
  quantity: number
  discount: number
  amount: number
  item_type: string | null
  sort_order: number
}

export interface PaymentPlan {
  id: string
  contract_id: string
  installment_no: number
  description: string | null
  plan_amount: number
  due_date: string
  status: string
  created_at: string
}

export interface PaymentPlanListItem {
  id: string
  contract_id: string
  contract_no: string
  contract_name: string
  installment_no: number
  description: string | null
  plan_amount: number
  due_date: string
  status: string
  received_amount: number
  created_at: string
}

export interface PaymentRecord {
  id: string
  plan_id: string
  contract_id: string
  received_amount: number
  received_date: string
  payment_method: string
  bank_reference: string | null
  received_by: string
  remark: string | null
  created_at: string
}

export interface ContractListItem {
  id: string
  contract_no: string
  customer_id: string
  contract_name: string
  contract_type: string
  certification_standard: string
  total_amount: number
  sign_date: string | null
  start_date: string | null
  end_date: string | null
  status: string
  sales_person: string
  created_at: string
}

export interface ContractDetail extends ContractListItem {
  opp_id: string | null
  service_scope: string
  tax_rate: number | null
  remark: string | null
  approved_by: string | null
  created_by: string | null
  updated_at: string
  items: ContractItem[]
  payment_plans: PaymentPlan[]
}

export const contractApi = {
  list(params: { page?: number; page_size?: number; status?: string; keyword?: string; customer_id?: string }) {
    return request.get<any, { code: number; data: ContractListItem[]; total: number }>('/contracts', { params })
  },
  get(id: string) {
    return request.get<any, { code: number; data: ContractDetail }>(`/contracts/${id}`)
  },
  create(data: Record<string, unknown>) {
    return request.post<any, { code: number; data: ContractDetail }>('/contracts', data)
  },
  update(id: string, data: Record<string, unknown>) {
    return request.put<any, { code: number; data: ContractDetail }>(`/contracts/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/contracts/${id}`)
  },
  listPaymentPlans(contractId: string) {
    return request.get<any, { code: number; data: PaymentPlan[] }>(`/contracts/${contractId}/payment-plans`)
  },
  listPaymentRecords(contractId: string) {
    return request.get<any, { code: number; data: PaymentRecord[] }>(`/contracts/${contractId}/payment-records`)
  },
  addPaymentRecord(contractId: string, data: Record<string, unknown>) {
    return request.post<any, { code: number; data: PaymentRecord }>(`/contracts/${contractId}/payment-records`, data)
  },
  listAllPaymentPlans(params: { page?: number; page_size?: number; status?: string; overdue?: boolean; keyword?: string }) {
    return request.get<any, { code: number; data: PaymentPlanListItem[]; total: number }>('/contracts/payment-plans/all', { params })
  },
}


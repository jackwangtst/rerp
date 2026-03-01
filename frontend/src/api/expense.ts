import request from './request'

export interface ExpenseListItem {
  id: string
  expense_type: string
  amount: number
  vendor: string | null
  paid_at: string
  quotation_id: string | null
  quote_no: string | null
  customer_id: string | null
  customer_name: string | null
  remark: string | null
  created_at: string
}

export interface ExpenseCreate {
  quotation_id?: string | null
  customer_id?: string | null
  project_id?: string | null
  expense_type: string
  amount: number
  vendor?: string | null
  paid_at: string
  remark?: string | null
}

export interface ExpenseStats {
  total_expense: number
  total_revenue: number
  profit: number
  profit_rate: number
  by_type: Record<string, number>
}

export const expenseApi = {
  list(params: Record<string, unknown>) {
    return request.get<any>('/expenses', { params }).then(r => r.data)
  },
  stats(params: Record<string, unknown> = {}) {
    return request.get<any>('/expenses/stats', { params }).then(r => r.data.data as ExpenseStats)
  },
  create(data: ExpenseCreate) {
    return request.post<any>('/expenses', data).then(r => r.data)
  },
  update(id: string, data: Partial<ExpenseCreate>) {
    return request.put<any>(`/expenses/${id}`, data).then(r => r.data)
  },
  remove(id: string) {
    return request.delete<any>(`/expenses/${id}`).then(r => r.data)
  },
}

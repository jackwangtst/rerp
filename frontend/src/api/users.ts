import request from './request'

export interface UserOut {
  id: string
  username: string
  full_name: string
  email: string | null
  phone: string | null
  role: string
  is_active: boolean
  last_login: string | null
  created_at: string
}

export const userApi = {
  list(params: { page?: number; page_size?: number }) {
    return request.get<any, { code: number; data: UserOut[]; total: number }>('/users', { params })
  },
  create(data: { username: string; full_name: string; password: string; role: string; email?: string; phone?: string }) {
    return request.post<any, { code: number; data: UserOut }>('/users', data)
  },
  update(id: string, data: { full_name?: string; email?: string; phone?: string; role?: string; is_active?: boolean; password?: string }) {
    return request.put<any, { code: number; data: UserOut }>(`/users/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/users/${id}`)
  },
}

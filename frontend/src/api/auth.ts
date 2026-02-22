import request from './request'

export interface LoginForm {
  username: string
  password: string
}

export interface UserInfo {
  id: string
  username: string
  full_name: string
  email: string | null
  role: string
}

export const authApi = {
  login(form: LoginForm) {
    const data = new FormData()
    data.append('username', form.username)
    data.append('password', form.password)
    return request.post<any, { code: number; data: { access_token: string } }>(
      '/auth/login',
      data,
    )
  },
  me() {
    return request.get<any, { code: number; data: UserInfo }>('/auth/me')
  },
}

import request from './request'

export interface ProjectListItem {
  id: string
  project_no: string
  contract_id: string
  customer_id: string
  standard: string
  certification_scope: string
  phase: string
  project_manager: string
  planned_start_date: string | null
  planned_end_date: string | null
  actual_end_date: string | null
  progress: number
  status: string
  created_at: string
}

export interface ProjectOut extends ProjectListItem {
  updated_at: string
}

export interface TaskListItem {
  id: string
  project_id: string
  task_name: string
  task_type: string
  assigned_to: string
  priority: string
  planned_start: string
  planned_end: string
  actual_start: string | null
  actual_end: string | null
  status: string
  created_at: string
}

export interface TaskOut extends TaskListItem {
  description: string | null
  co_auditors: string[]
  actual_hours: number | null
  result: string | null
  created_by: string
  updated_at: string
}

export const projectApi = {
  list(params: { page?: number; page_size?: number; status?: string; keyword?: string; customer_id?: string }) {
    return request.get<any, { code: number; data: ProjectListItem[]; total: number }>('/projects', { params })
  },
  get(id: string) {
    return request.get<any, { code: number; data: ProjectOut }>(`/projects/${id}`)
  },
  create(data: Record<string, unknown>) {
    return request.post<any, { code: number; data: ProjectOut }>('/projects', data)
  },
  update(id: string, data: Record<string, unknown>) {
    return request.put<any, { code: number; data: ProjectOut }>(`/projects/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/projects/${id}`)
  },
  listTasks(projectId: string) {
    return request.get<any, { code: number; data: TaskOut[] }>(`/projects/${projectId}/tasks`)
  },
}

export const taskApi = {
  list(params: { page?: number; page_size?: number; status?: string; keyword?: string; assigned_to?: string }) {
    return request.get<any, { code: number; data: TaskListItem[]; total: number }>('/tasks', { params })
  },
  create(data: Record<string, unknown>) {
    return request.post<any, { code: number; data: TaskOut }>('/tasks', data)
  },
  update(id: string, data: Record<string, unknown>) {
    return request.put<any, { code: number; data: TaskOut }>(`/tasks/${id}`, data)
  },
  delete(id: string) {
    return request.delete(`/tasks/${id}`)
  },
}

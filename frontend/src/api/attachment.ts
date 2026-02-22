import request from './request'

export interface Attachment {
  id: string
  entity_type: string
  entity_id: string
  file_name: string
  file_url: string
  file_size: number | null
  mime_type: string | null
  uploaded_by: string | null
  created_at: string
}

export function getAttachments(entity_type: string, entity_id: string) {
  return request.get<Attachment[]>('/attachments', { params: { entity_type, entity_id } })
}

export function uploadAttachment(entity_type: string, entity_id: string, file: File) {
  const form = new FormData()
  form.append('file', file)
  return request.post<Attachment>(`/attachments?entity_type=${entity_type}&entity_id=${entity_id}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function deleteAttachment(id: string) {
  return request.delete(`/attachments/${id}`)
}

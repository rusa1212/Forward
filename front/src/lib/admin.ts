import { api } from './api'
import type { AdminEmployee, AdminUser } from '@/types'

/** back/app/api/v1/admin.py의 _serialize_employee()/_serialize_user()가 내려주는 필드 그대로. */

export function listEmployees() {
  return api.get<AdminEmployee[]>('/admin/employees').then(({ data }) => data)
}

export function createEmployee(body: { empId: string; name: string; department?: string }) {
  return api.post<AdminEmployee>('/admin/employees', body).then(({ data }) => data)
}

export function deleteEmployee(empId: string) {
  return api.delete(`/admin/employees/${empId}`)
}

export function listUsers() {
  return api.get<AdminUser[]>('/admin/users').then(({ data }) => data)
}

export function deleteUser(userId: string) {
  return api.delete(`/admin/users/${userId}`)
}

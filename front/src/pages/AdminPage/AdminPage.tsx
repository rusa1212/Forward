import { useState } from 'react'
import { useAdminEmployees } from '@/hooks/useAdminEmployees'
import { useAdminUsers } from '@/hooks/useAdminUsers'

export default function AdminPage() {
  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-800">관리자 페이지</h1>
        <p className="text-sm text-gray-500 mt-1">사원 명부를 관리하고 가입자 계정을 조회·삭제합니다.</p>
      </div>
      <EmployeesSection />
      <UsersSection />
    </div>
  )
}

function EmployeesSection() {
  const { employees, addEmployee, removeEmployee, loading, error } = useAdminEmployees()
  const [empId, setEmpId] = useState('')
  const [name, setName] = useState('')
  const [department, setDepartment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [rowError, setRowError] = useState('')

  const handleAdd = async () => {
    if (!empId.trim() || !name.trim() || submitting) return
    setSubmitting(true)
    const added = await addEmployee({ empId: empId.trim(), name: name.trim(), department: department.trim() || undefined })
    setSubmitting(false)
    if (added) {
      setEmpId('')
      setName('')
      setDepartment('')
    }
  }

  const handleRemove = async (targetEmpId: string, joined: boolean) => {
    if (joined) {
      setRowError('이미 가입한 사원은 명부에서 삭제할 수 없습니다.')
      return
    }
    setRowError('')
    await removeEmployee(targetEmpId)
  }

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
        <h3 className="text-sm font-semibold text-gray-800 mb-3">사원 명부 등록</h3>
        <div className="flex gap-2 flex-wrap">
          <input
            value={empId}
            onChange={e => setEmpId(e.target.value)}
            className="flex-1 min-w-[140px] border border-gray-200 rounded-xl px-3.5 py-2 text-sm focus:outline-none focus:border-[#457b9d] focus:ring-2 focus:ring-[#457b9d]/20 transition"
            placeholder="사번"
          />
          <input
            value={name}
            onChange={e => setName(e.target.value)}
            className="flex-1 min-w-[140px] border border-gray-200 rounded-xl px-3.5 py-2 text-sm focus:outline-none focus:border-[#457b9d] focus:ring-2 focus:ring-[#457b9d]/20 transition"
            placeholder="이름"
          />
          <input
            value={department}
            onChange={e => setDepartment(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleAdd()}
            className="flex-1 min-w-[140px] border border-gray-200 rounded-xl px-3.5 py-2 text-sm focus:outline-none focus:border-[#457b9d] focus:ring-2 focus:ring-[#457b9d]/20 transition"
            placeholder="부서 (선택)"
          />
          <button onClick={handleAdd} disabled={submitting} className="bg-[#1d3557] text-white px-5 py-2 rounded-xl text-sm font-semibold hover:bg-[#16293f] transition-colors disabled:opacity-40">등록</button>
        </div>
        {error && <p className="text-xs text-red-500 mt-2">{error}</p>}
        {rowError && <p className="text-xs text-red-500 mt-2">{rowError}</p>}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-5 py-3.5 border-b border-gray-100 flex items-center gap-2">
          <span className="text-sm font-semibold text-gray-800">사원 명부</span>
          <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">{employees.length}명</span>
        </div>
        {loading ? (
          <div className="py-12 text-center text-gray-400 text-sm">불러오는 중...</div>
        ) : employees.length === 0 ? (
          <div className="py-12 text-center text-gray-400 text-sm">등록된 사원이 없습니다.</div>
        ) : (
          <div className="divide-y divide-gray-50">
            {employees.map(emp => (
              <div key={emp.empId} className="px-5 py-3.5 flex items-center justify-between hover:bg-gray-50 transition-colors">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-gray-800">{emp.name}</span>
                  <span className="text-xs text-gray-400">{emp.empId}</span>
                  {emp.department && <span className="text-xs text-gray-400">· {emp.department}</span>}
                  {emp.joined && (
                    <span className="text-[10px] bg-green-50 text-green-600 px-1.5 py-0.5 rounded border border-green-100 font-medium">가입완료</span>
                  )}
                </div>
                <button
                  onClick={() => handleRemove(emp.empId, emp.joined)}
                  disabled={emp.joined}
                  className="p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-gray-300"
                  title={emp.joined ? '이미 가입한 사원은 삭제할 수 없습니다' : '삭제'}
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function UsersSection() {
  const { users, removeUser, loading, error } = useAdminUsers()

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="px-5 py-3.5 border-b border-gray-100 flex items-center gap-2">
        <span className="text-sm font-semibold text-gray-800">가입자 목록</span>
        <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">{users.length}명</span>
      </div>
      {error && <p className="text-xs text-red-500 px-5 pt-3">{error}</p>}
      {loading ? (
        <div className="py-12 text-center text-gray-400 text-sm">불러오는 중...</div>
      ) : users.length === 0 ? (
        <div className="py-12 text-center text-gray-400 text-sm">가입한 계정이 없습니다.</div>
      ) : (
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50/80 border-b border-gray-100">
              <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500">이름</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500">사번</th>
              <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500">이메일</th>
              <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 w-20">권한</th>
              <th className="text-center px-4 py-3 text-xs font-semibold text-gray-500 w-16">삭제</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id} className="border-b border-gray-50 last:border-b-0 hover:bg-gray-50/50 transition-colors">
                <td className="px-5 py-3 text-sm text-gray-800 font-medium">{u.name}</td>
                <td className="px-4 py-3 text-xs text-gray-500">{u.empId}</td>
                <td className="px-4 py-3 text-xs text-gray-500">{u.email}</td>
                <td className="px-4 py-3 text-center">
                  {u.isAdmin ? (
                    <span className="text-[10px] bg-[#1d3557] text-white px-1.5 py-0.5 rounded font-bold">관리자</span>
                  ) : (
                    <span className="text-[10px] text-gray-400">일반</span>
                  )}
                </td>
                <td className="px-4 py-3 text-center">
                  <button onClick={() => removeUser(u.id)} className="p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors" title="계정 삭제">
                    <svg className="w-4 h-4 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

import { useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAdminEmployees } from '@/hooks/useAdminEmployees'
import { useAdminUsers } from '@/hooks/useAdminUsers'

type AdminTab = 'employees' | 'users'

export default function AdminPage() {
  const [tab, setTab] = useState<AdminTab>('employees')

  return (
    <div className="max-w-[1200px] mx-auto px-8 py-7 space-y-5">
      <div className="rise rise-1 flex items-center justify-between">
        <div>
          <h1 className="text-[22px] font-extrabold text-strong tracking-[-0.3px]">관리자</h1>
          <p className="mt-1 text-[13px] text-muted2">사원 명부를 관리하고 가입자 계정을 조회·삭제합니다.</p>
        </div>
        <div className="flex items-center bg-[#eef2f6] rounded-full p-[3px]">
          {([['employees', '직원 명부'], ['users', '가입 사용자']] as [AdminTab, string][]).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={cn(
                'h-[30px] px-4 rounded-full text-[13px] transition-all whitespace-nowrap',
                tab === key ? 'bg-white text-strong font-semibold shadow-seg' : 'text-sub font-medium hover:text-strong'
              )}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="rise rise-2">
        {tab === 'employees' ? <EmployeesSection /> : <UsersSection />}
      </div>
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

  const inputCls =
    'h-[38px] px-3 bg-white border border-line rounded-[10px] text-sm text-strong placeholder:text-muted2 focus:outline-none focus:border-primary2 focus:ring-2 focus:ring-primary2/20 transition-all'

  return (
    <div className="bg-surface border border-line rounded-xl overflow-hidden">
      {/* 액션바 */}
      <div className="px-7 py-4 border-b border-line flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-strong">사원 명부</span>
          <span className="px-2 py-0.5 rounded-full bg-soft text-primary2 text-[11px] font-bold tabular-nums whitespace-nowrap">{employees.length}명</span>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <input value={empId} onChange={e => setEmpId(e.target.value)} placeholder="사번" className={`${inputCls} w-32`} />
          <input value={name} onChange={e => setName(e.target.value)} placeholder="이름" className={`${inputCls} w-32`} />
          <input value={department} onChange={e => setDepartment(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleAdd()} placeholder="부서 (선택)" className={`${inputCls} w-36`} />
          <button
            onClick={handleAdd}
            disabled={submitting}
            className="pressable h-[38px] px-4 rounded-[10px] bg-primary2 hover:bg-primary-hover text-white text-[13px] font-semibold flex items-center gap-1 transition-colors disabled:opacity-40"
          >
            <Plus className="w-3.5 h-3.5" strokeWidth={2.2} />
            명부에 추가
          </button>
        </div>
      </div>
      {(error || rowError) && <p className="px-7 pt-3 text-xs text-danger">{error || rowError}</p>}

      {loading ? (
        <div className="py-14 text-center text-sm text-muted2">불러오는 중...</div>
      ) : employees.length === 0 ? (
        <div className="py-14 text-center text-sm text-muted2">등록된 사원이 없습니다.</div>
      ) : (
        <div className="overflow-x-auto">
          <div className="min-w-[720px]">
            <div className="grid grid-cols-[120px_minmax(0,1fr)_160px_120px_64px] items-center gap-2 px-7 h-10 bg-thead border-b border-line">
              <span className="text-xs font-semibold text-muted2">사번</span>
              <span className="text-xs font-semibold text-muted2">이름</span>
              <span className="text-xs font-semibold text-muted2">부서</span>
              <span className="text-xs font-semibold text-muted2 text-center">가입 상태</span>
              <span className="text-xs font-semibold text-muted2 text-center">삭제</span>
            </div>
            {employees.map((emp, i, arr) => (
              <div key={emp.empId} className={`grid grid-cols-[120px_minmax(0,1fr)_160px_120px_64px] items-center gap-2 px-7 py-3 hover:bg-subtle transition-colors ${i < arr.length - 1 ? 'border-b border-line' : ''}`}>
                <span className="text-[13px] text-body tabular-nums">{emp.empId}</span>
                <span className="text-sm font-semibold text-strong">{emp.name}</span>
                <span className="text-[13px] text-body">{emp.department || '—'}</span>
                <div className="flex justify-center">
                  {emp.joined ? (
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold text-success bg-[rgba(18,183,105,0.10)] whitespace-nowrap">가입 완료</span>
                  ) : (
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold text-sub bg-[#f2f4f7] whitespace-nowrap">대기</span>
                  )}
                </div>
                <button
                  onClick={() => handleRemove(emp.empId, emp.joined)}
                  disabled={emp.joined}
                  aria-label={emp.joined ? '이미 가입한 사원은 삭제할 수 없습니다' : `${emp.name} 삭제`}
                  title={emp.joined ? '이미 가입한 사원은 삭제할 수 없습니다' : '삭제'}
                  className="pressable justify-self-center p-1.5 rounded-lg text-faint hover:text-danger hover:bg-[rgba(240,68,56,0.06)] transition-colors disabled:opacity-30 disabled:hover:text-faint disabled:hover:bg-transparent"
                >
                  <Trash2 className="w-4 h-4" strokeWidth={1.8} />
                </button>
              </div>
            ))}
            <div className="px-7 py-3 border-t border-line flex items-center justify-between">
              <span className="text-xs text-muted2">가입 완료된 사원은 명부에서 삭제할 수 없습니다.</span>
              <span className="text-xs text-muted2 tabular-nums whitespace-nowrap">1–{employees.length} / {employees.length}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function UsersSection() {
  const { users, removeUser, loading, error } = useAdminUsers()

  return (
    <div className="bg-surface border border-line rounded-xl overflow-hidden">
      <div className="px-7 py-4 border-b border-line flex items-center gap-2">
        <span className="text-sm font-bold text-strong">가입 사용자</span>
        <span className="px-2 py-0.5 rounded-full bg-soft text-primary2 text-[11px] font-bold tabular-nums whitespace-nowrap">{users.length}명</span>
      </div>
      {error && <p className="px-7 pt-3 text-xs text-danger">{error}</p>}
      {loading ? (
        <div className="py-14 text-center text-sm text-muted2">불러오는 중...</div>
      ) : users.length === 0 ? (
        <div className="py-14 text-center text-sm text-muted2">가입한 계정이 없습니다.</div>
      ) : (
        <div className="overflow-x-auto">
          <div className="min-w-[720px]">
            <div className="grid grid-cols-[minmax(0,1fr)_120px_220px_100px_64px] items-center gap-2 px-7 h-10 bg-thead border-b border-line">
              <span className="text-xs font-semibold text-muted2">이름</span>
              <span className="text-xs font-semibold text-muted2">사번</span>
              <span className="text-xs font-semibold text-muted2">이메일</span>
              <span className="text-xs font-semibold text-muted2 text-center">권한</span>
              <span className="text-xs font-semibold text-muted2 text-center">삭제</span>
            </div>
            {users.map((u, i, arr) => (
              <div key={u.id} className={`grid grid-cols-[minmax(0,1fr)_120px_220px_100px_64px] items-center gap-2 px-7 py-3 hover:bg-subtle transition-colors ${i < arr.length - 1 ? 'border-b border-line' : ''}`}>
                <span className="text-sm font-semibold text-strong truncate">{u.name}</span>
                <span className="text-[13px] text-body tabular-nums">{u.empId}</span>
                <span className="text-[13px] text-body truncate">{u.email}</span>
                <div className="flex justify-center">
                  {u.isAdmin ? (
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold text-primary2 bg-soft whitespace-nowrap">관리자</span>
                  ) : (
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold text-sub bg-[#f2f4f7] whitespace-nowrap">일반</span>
                  )}
                </div>
                <button
                  onClick={() => removeUser(u.id)}
                  aria-label={`${u.name} 계정 삭제`}
                  title="계정 삭제"
                  className="pressable justify-self-center p-1.5 rounded-lg text-faint hover:text-danger hover:bg-[rgba(240,68,56,0.06)] transition-colors"
                >
                  <Trash2 className="w-4 h-4" strokeWidth={1.8} />
                </button>
              </div>
            ))}
            <div className="px-7 py-3 border-t border-line flex items-center justify-end">
              <span className="text-xs text-muted2 tabular-nums whitespace-nowrap">1–{users.length} / {users.length}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

import { api } from './api'
import type { AlertSettings } from '@/types'

/**
 * 마이페이지 알림 설정 — back/app/api/v1/me.py의 /me/alert-settings.
 * 모두 토큰 필요. (docs/fe/alert-settings-API-제안.md)
 */

/** 저장한 적 없는 사용자는 BE가 화면 기본값(매일/D-7/대시보드 on/이메일 off)을 그대로 내려준다. */
export function getAlertSettings() {
  return api.get<AlertSettings>('/me/alert-settings').then(({ data }) => data)
}

/** 4개 필드 전부 보낸다(부분 수정 아님) — 화면 저장 버튼이 한 번에 다 보내는 것과 맞춘다. */
export function saveAlertSettings(settings: AlertSettings) {
  return api.put<AlertSettings>('/me/alert-settings', settings).then(({ data }) => data)
}

// 设备模块
// 后端需实现：
//   GET    /api/devices      → Device[]
//   POST   /api/devices      { name, model, lab_id, total, available } → Device
//   PUT    /api/devices/:id  同上 → Device
//   DELETE /api/devices/:id  → null

import { del, get, post, put } from './request'
import type { Device } from './types'

export const deviceApi = {
  list() {
    return get<Device[]>('/devices')
  },

  create(data: Omit<Device, 'id' | 'lab_name'>) {
    return post<Device>('/devices', data)
  },

  update(id: number, data: Partial<Device>) {
    return put<Device>(`/devices/${id}`, data)
  },

  remove(id: number) {
    return del<null>(`/devices/${id}`)
  },
}

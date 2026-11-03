// 实验室模块
// 后端需实现：
//   GET    /api/labs        → Lab[]
//   POST   /api/labs        { name, location, capacity, is_open } → Lab
//   PUT    /api/labs/:id    同上 → Lab
//   DELETE /api/labs/:id    → null

import { del, get, post, put } from './request'
import type { Lab } from './types'

export const labApi = {
  list() {
    return get<Lab[]>('/labs')
  },

  create(data: Omit<Lab, 'id' | 'device_count'>) {
    return post<Lab>('/labs', data)
  },

  update(id: number, data: Partial<Lab>) {
    return put<Lab>(`/labs/${id}`, data)
  },

  remove(id: number) {
    return del<null>(`/labs/${id}`)
  },
}

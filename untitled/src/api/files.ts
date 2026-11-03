// ============================================================
// 文件模块：文件上传接口定义
// 对应后端 POST /files/upload（app/api/files.py）
// ============================================================

// upload 是 utils/request.ts 里的文件上传专用方法（FormData 格式）
import { upload } from '@/utils/request'
import type { UploadResult } from './types'

export const fileApi = {
  // 上传文件：参数是浏览器 File 对象（input 选中的文件 / el-upload 回调里拿到的那种）
  // 成功返回文件信息，其中 url（相对路径）用于存库和显示
  uploadFile(file: File) {
    return upload<UploadResult>('/files/upload', file)
  },
}

/// <reference types="vite/client" />
// 上面这行：引入 Vite 的类型定义，让 TS 认识 import.meta.env 等用法

// 给自定义环境变量补充类型声明：
// 声明后代码里写 import.meta.env.VITE_API_BASE 才有类型提示、不会报红线
interface ImportMetaEnv {
  readonly VITE_API_BASE?: string // readonly：只读，不允许修改；?: 可选
}

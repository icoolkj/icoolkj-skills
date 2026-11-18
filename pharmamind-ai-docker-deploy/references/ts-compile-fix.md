# 前端 TS 编译报错修复

当 `vite build` 阶段报类型错误导致构建失败时使用。本 skill 覆盖两类最高频报错。

## 报错清单

| 报错码 | 含义 | 典型信息 |
| ------ | ---- | -------- |
| TS7006 | 参数隐式 any | `Parameter 'xxx' implicitly has an 'any' type` |
| TS2769 | 插件/重载类型不匹配 | `No overload matches this call` |

## 方案 A：快速兜底（先跑通，生产后再优化类型）

适合"今晚必须部署成功"的场景，代价是放弃部分类型约束。

### A1. 修改前端目录 tsconfig.json

直接复制本 skill 的 `assets/tsconfig.json` 覆盖前端目录的 `tsconfig.json`。关键差异：

```json
{
  "compilerOptions": {
    "skipLibCheck": true,
    "noImplicitAny": false,
    "strict": true
  }
}
```

- `noImplicitAny: false`：消除 TS7006。
- `skipLibCheck: true`：跳过第三方声明文件检查，规避依赖版本间的类型冲突。
- 保留 `strict: true`，让其余严格检查继续生效。

### A2. vite 插件类型报错强制绕过

在 `vite.config.ts` 中对报错插件加 `as any`：

```ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import xxxPlugin from 'xxx-plugin'

export default defineConfig({
  plugins: [
    vue(),
    xxxPlugin() as any
  ]
})
```

## 方案 B：规范修复（推荐用于正式版本）

1. **补全回调参数类型**：定位 TS7006 报出的文件与行号，给回调参数补类型，例如 `(path: string) => {}`、`(item: Item) => {}`。
2. **对齐版本**：统一 `vite` 与 `@vitejs/plugin-vue` 等插件的版本号，避免插件 API 类型与主版本不匹配导致 TS2769。
   - 对照官方兼容性矩阵，把 `package.json` 中相关依赖升到彼此兼容的版本，删除旧 `node_modules` 与 lock 文件后重装。
3. 修复后移除 `as any` 与 `noImplicitAny: false`，恢复完整类型检查。

## 决策建议

- 首次部署 / 演示环境：用方案 A 快速跑通。
- 生产 / 长期维护：用方案 B，把类型补全作为独立任务处理。

## 验证

修复后重新执行流程5的构建命令，确认不再出现 TS 报错：

```powershell
docker compose up -d --build
```

# PharmaMind-AI Docker Deploy 1.0.0

面向 PharmaMind-AI 医药 RAG 知识库系统的本地 Docker Compose 部署运维技能。把一次成功的部署路径（镜像源限流规避、TS 编译报错修复、pgvector 连接、容器健康检查、故障排查）固化为可复用流程与脚本。

## 技术栈

- 后端：FastAPI（Python 3.12）
- 前端：Vue3 + TypeScript + Vite
- 数据库：pgvector（基于 PostgreSQL 16）
- 编排：Docker Compose

## 何时使用

- 首次部署 / 重建 PharmaMind-AI。
- `docker compose up --build` 报 429 限流。
- 前端 `vite build` 报 TS7006 / TS2769。
- DBeaver / pgAdmin 连不上 5432，或误用浏览器访问数据库端口。
- 容器起来后前端白屏 / 500，需要看日志排障。

## 目录结构

```
pharmamind-ai-docker-deploy/
├─ SKILL.md                        # 技能主文档：工作流决策树 + 8 段流程
├─ README.md
├─ CHANGELOG.md
├─ scripts/
│  ├─ pre-check.ps1                # 端口 + Docker 状态预检查
│  ├─ pull-base-images.ps1         # 串行预拉取基础镜像（防 429）
│  ├─ start.ps1                    # down + up -d --build 一键启动
│  └─ logs-follow.ps1              # 实时日志（支持 -Service 过滤）
├─ assets/
│  └─ tsconfig.json                # TS 快速兜底配置模板
└─ references/
   ├─ ts-compile-fix.md            # TS7006/TS2769 两套修复方案
   ├─ db-connection.md             # pgvector 连接参数与验证
   └─ troubleshooting.md           # 故障排查对照表
```

## 典型用法

按顺序执行（在 `compose.yaml` 所在目录）：

```powershell
# 1. 前置检查（只读）
./scripts/pre-check.ps1

# 2. Docker Engine JSON 清空 registry-mirrors 后，串行预拉取镜像
./scripts/pull-base-images.ps1

# 3. 若 vite build 报 TS 错误：复制 assets/tsconfig.json 覆盖前端配置，或按 references/ts-compile-fix.md 规范修复

# 4. 构建并后台启动
./scripts/start.ps1

# 5. 看日志确认就绪
./scripts/logs-follow.ps1
./scripts/logs-follow.ps1 -Service backend

# 6. 用数据库客户端连接（参数从 compose.yaml 读取），不要用浏览器访问 5432
```

端口与地址：

- 前端 http://localhost:5173
- 后端接口 http://localhost:8000，文档 http://localhost:8000/docs
- 数据库 localhost:5432（仅客户端连接）

## 核心原则

1. 先预拉取再构建，杜绝并发拉取触发 429。
2. 不长期依赖镜像加速，靠本地缓存兜底。
3. 5432 是 TCP 不是 HTTP，浏览器打不开是正常的。
4. 数据库参数一律从 compose.yaml 读取，不臆测。
5. 就绪看明确日志标志，不靠感觉。

## 环境

- Windows 10/11，PowerShell 5.1+
- Docker Desktop（WSL2 后端正常）
- 宿主机 5173 / 8000 / 5432 端口可用

## 版本

版本号统一维护在 `SKILL.md` frontmatter 的 `version` 字段，详见 `CHANGELOG.md`。

## 许可

MIT

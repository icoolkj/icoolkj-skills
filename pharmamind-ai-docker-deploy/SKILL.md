---
name: pharmamind-ai-docker-deploy
description: |
  PharmaMind-AI 医药 RAG 知识库项目的本地 Docker Compose 部署运维技能。覆盖从前置端口检查、Docker 镜像源限流(429)规避、基础镜像预拉取、前端 Vue3+TS 编译报错(TS7006/TS2769)修复、compose 构建启动、容器健康检查、pgvector 数据库连接指导到故障排查的全链路。
  当用户要求部署/启动 PharmaMind-AI、docker compose up 报 429 toomanyrequests、Vite build 报 TS 类型错误、DBeaver/pgAdmin 连不上 5432、容器启动后前端 500 或白屏、查看容器日志排查等问题时使用本技能。
  触发词：pharmamind、pharmamind-ai、pgvector部署、docker compose 429限流、vite build TS7006、pg 5432浏览器打不开、PharmaMind 部署、医药RAG部署。
agent_created: true
version: 1.0.0
display_name: PharmaMind-AI Docker 部署运维
display_name_en: PharmaMind-AI Docker Deploy
description_zh: |
  PharmaMind-AI 医药 RAG 知识库项目的本地 Docker Compose 部署运维技能，覆盖镜像源限流、TS 编译报错、pgvector 连接误区、健康检查与故障排查全链路。
description_en: |
  Local Docker Compose deployment and operations skill for the PharmaMind-AI medical RAG knowledge base project. Covers registry rate limits, TypeScript build errors, pgvector connection pitfalls, health checks and troubleshooting.
author: icoolkj
license: MIT
metadata:
  homepage: https://icoolkj.com
  repository: https://github.com/icoolkj/icoolkj-skills
  contact: icoolkj@163.com
  qq: "594047667"
allowed-tools: Bash(powershell:*)
---

# PharmaMind-AI Docker 部署运维 Skill

> 面向 PharmaMind-AI 医药 RAG 知识库系统的标准化本地部署流程。
> 技术栈：FastAPI(Python 3.12) + Vue3+TS+Vite + pgvector(pg16) + Docker Compose。
> 目标：规避国内镜像源限流、编译报错、数据库连接认知坑，把一次成功的部署路径固化为可复用流程。

## 何时触发

用户出现以下意图时使用本技能：
- 部署 / 启动 / 重建 PharmaMind-AI（"帮我把这个医药知识库跑起来"）。
- `docker compose up --build` 报 `429 toomanyrequests` 或镜像拉取卡住。
- 前端 `vite build` 报 `TS7006` / `TS2769` 等类型错误。
- DBeaver / Navicat / pgAdmin 连不上 5432，或误用浏览器访问数据库端口。
- 容器起来后前端白屏 / 500、后端未就绪、需要看容器日志排障。

## 核心原则（务必遵守）

1. **先预拉取，后构建**：绝不直接 `compose up --build` 并发拉取多个基础镜像，那是触发 429 的头号原因。按序手动 `docker pull`，全部成功后才构建。
2. **不长期依赖镜像加速**：公益镜像源（1ms.run / ustc 等）极易限流，且 buildx 构建阶段会绕过 `registry-mirrors`。清空 mirror 配置，靠本地缓存兜底；只有网络极差时才临时切 `hub.rat.dev`。
3. **5432 是 TCP 不是 HTTP**：PostgreSQL 端口不能用浏览器打开，必须用数据库客户端连接。这是最高频的认知误区。
4. **连接参数从 compose.yaml 读取**：数据库名 / 用户 / 密码不要臆测，一律从 `compose.yaml` 的 `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` 读取。
5. **就绪有明确标志**：数据库看 `database system is ready to accept connections`，后端看 `Application startup complete`，不要靠"感觉"判断。
6. **先诊断后动手**：改配置、停宿主机服务、改端口映射前，先用 `pre-check.ps1` 确认真实状态。

## 工作流决策树

```
用户请求部署/排障
├─ 首次部署 → 依次执行 流程1 → 流程2 → 流程3 → 流程4(仅当编译报错) → 流程5 → 流程6 → 流程7
├─ 报 429 限流 → 跳到 流程2 + 流程3，然后回到 流程5
├─ 报 TS 编译错误 → 跳到 流程4，然后回到 流程5
├─ 连不上数据库 → 跳到 流程7 + 流程8
└─ 容器异常/前端500 → 跳到 流程6 看日志 + 流程8
```

## 部署工作流

### 流程1：前置检查 pre_check

运行 `scripts/pre-check.ps1`（或手动执行其中的命令）检查 5173 / 8000 / 5432 端口占用与 Docker 状态。

- 5432 被宿主机本地 PostgreSQL 占用 → 二选一：停宿主机 PG，或把 `compose.yaml` 端口映射改为 `"5433:5432"`（同时后续客户端连接端口改为 5433）。
- Docker Daemon 异常 → 重启 Docker Desktop 再继续。

### 流程2：Docker Daemon 镜像源配置 docker_daemon_config

在 Docker Desktop → Settings → Docker Engine 的 JSON 中，清空 `registry-mirrors`（避免并发构建触发上游限流），保留 builder GC 配置：

```json
{
  "builder": { "gc": { "defaultKeepStorage": "20GB", "enabled": true } },
  "experimental": false
}
```

Apply & Restart。仅当网络极差时临时把 `"registry-mirrors": ["https://hub.rat.dev"]` 加回去。

### 流程3：镜像预拉取 image_prepull（防 429 关键步骤）

运行 `scripts/pull-base-images.ps1`，按序拉取四个基础镜像：

```powershell
docker pull python:3.12-slim
docker pull node:22-alpine
docker pull nginx:1.27-alpine
docker pull pgvector/pgvector:pg16
```

全部返回 `Status: Downloaded newer image` 或 `Image is up to date` 后再进入下一步。

### 流程4：前端 TS 编译报错修复 frontend_ts_fix

仅当 `vite build` 报 `TS7006`（参数隐式 any）或 `TS2769`（插件类型不匹配）时执行。详见 `references/ts-compile-fix.md`。

- 快速兜底：`assets/tsconfig.json` 设置 `noImplicitAny: false`，vite 插件加 `as any`。
- 规范修复：补全回调参数类型、对齐 vite 与插件版本。
- 若需直接替换，把 `assets/tsconfig.json` 复制到前端目录的 `tsconfig.json`。

### 流程5：构建并启动 compose_build_up

运行 `scripts/start.ps1`（内部执行 `docker compose down` 后 `docker compose up -d --build`），或手动前台启动观察日志：

```powershell
docker compose down
docker compose up --build
```

### 流程6：健康检查 health_check

运行 `scripts/logs-follow.ps1` 看实时日志，确认三个容器均 running：

- `frontend-1`：`5173:80` → http://localhost:5173
- `backend-1`：`8000:8000` → http://localhost:8000（接口文档 http://localhost:8000/docs）
- `db-1`：`pgvector/pgvector:pg16`，`5432:5432`

就绪标志：数据库 `database system is ready to accept connections`；后端 `Application startup complete`。

### 流程7：pgvector 数据库连接指南 connect_db_guide

详见 `references/db-connection.md`。要点：用 DBeaver / Navicat / pgAdmin / psql 连接，Host=localhost，Port=5432，库名/用户/密码从 compose.yaml 读取。容器内验证：

```powershell
docker exec -it db-1 psql -U {POSTGRES_USER} -d {POSTGRES_DB}
```
```sql
SELECT * FROM pg_extension WHERE extname='vector';
```

### 流程8：故障排查 trouble_shooting

详见 `references/troubleshooting.md` 的现象-根因-方案对照表，覆盖 429、TS 报错、前端 500、5432 连不上、npm install 卡死等高频问题。

## 收尾验证清单

- [ ] 前端页面 http://localhost:5173 正常加载无白屏
- [ ] 后端文档 http://localhost:8000/docs 可以打开
- [ ] DBeaver 可正常连接 pgvector 数据库
- [ ] 向量扩展 vector 已启用

## 资源索引

- `scripts/pre-check.ps1`：端口与 Docker 状态预检查
- `scripts/pull-base-images.ps1`：按顺序预拉取基础镜像
- `scripts/start.ps1`：一键 down + up -d --build
- `scripts/logs-follow.ps1`：实时跟踪容器日志
- `assets/tsconfig.json`：TS 快速兜底配置模板
- `references/ts-compile-fix.md`：TS 编译报错两套修复方案
- `references/db-connection.md`：pgvector 连接参数与验证
- `references/troubleshooting.md`：故障排查对照表

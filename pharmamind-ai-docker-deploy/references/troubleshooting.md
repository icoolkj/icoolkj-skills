# 故障排查手册

按现象查根因与处理方案。定位问题时先跑 `scripts/pre-check.ps1` 和 `scripts/logs-follow.ps1` 收集信息。

## 现象-根因-方案对照表

| 现象 | 根因 | 处理方案 |
| ---- | ---- | ---- |
| build 报 `429 toomanyrequests` | 镜像源限流，compose 并发拉取多个基础镜像 | 停止构建；清空 Docker Engine 的 registry-mirrors；运行 `pull-base-images.ps1` 串行预拉取；等待 5~10 分钟后重试构建 |
| buildx 构建阶段仍触发限流 | 公益镜像源不稳定，且 buildx 绕过 registry-mirrors | 不长期依赖镜像加速，靠本地预拉取缓存；网络极差时临时切 `https://hub.rat.dev` |
| `TS7006` / `TS2769` | Vue3 + TS 严格类型校验 / 插件版本不匹配 | 快速兜底：复制 `assets/tsconfig.json` 设 `noImplicitAny: false`，插件加 `as any`；规范修复见 `ts-compile-fix.md` |
| 容器启动后 CPU 0%、前端 500/白屏 | 后端仍在等待数据库初始化或迁移脚本报错 | 等待约 30s；`docker compose logs -f backend` 看数据库迁移/初始化日志，定位具体报错 |
| DBeaver 连不上 5432 | 宿主机端口占用 / 容器未就绪 / 参数错误 | `pre-check.ps1` 查端口；`docker compose logs db` 看就绪日志；核对参数与 compose.yaml 一致；见 `db-connection.md` |
| 浏览器打不开 `localhost:5432` | 认知误区：5432 是 PostgreSQL TCP 端口，不是 HTTP | 用数据库客户端连接，不要用浏览器；前端地址是 5173，后端接口是 8000 |
| `npm install` 卡死 | 访问 npm 官方源慢 | 在前端 Dockerfile 内换源：`RUN npm config set registry https://registry.npmmirror.com` |
| 5432 被宿主机 PostgreSQL 占用 | 本地已装 PostgreSQL 占用同端口 | 停宿主机 PG 服务，或把 compose.yaml 映射改为 `"5433:5432"`，客户端端口同步改 5433 |
| Docker Daemon 不可用 | Docker Desktop 未启动 / WSL2 后端异常 | 重启 Docker Desktop，确认 WSL2 状态后重跑 `pre-check.ps1` |

## 诊断命令速查

```powershell
# 端口与 Docker 状态
./scripts/pre-check.ps1

# 容器运行状态
docker compose ps

# 全部实时日志
./scripts/logs-follow.ps1

# 单服务日志
./scripts/logs-follow.ps1 -Service backend

# 容器内验证数据库扩展
docker exec -it db-1 psql -U {POSTGRES_USER} -d {POSTGRES_DB}
```

## 就绪标志速查

- 数据库：`database system is ready to accept connections`
- 后端：`Application startup complete`（FastAPI）
- 前端：http://localhost:5173 页面正常渲染无白屏

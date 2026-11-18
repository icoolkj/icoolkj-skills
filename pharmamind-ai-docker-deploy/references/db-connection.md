# pgvector 数据库连接指南

## 关键认知：5432 是 TCP 协议端口，不是 HTTP

PostgreSQL 使用私有 TCP 协议，**不能用浏览器通过 http/https 打开**。在浏览器访问 `http://localhost:5432` 失败是正常的，不代表数据库有问题。必须用数据库客户端连接。

## 连接参数

正确的连接方式：DBeaver / Navicat / pgAdmin / psql cli。

| 参数 | 取值 |
| ---- | ---- |
| Host | localhost |
| Port | 5432（若 compose 映射改为 5433:5432，则填 5433） |
| Database | 从 `compose.yaml` 的 `POSTGRES_DB` 读取 |
| Username | 从 `compose.yaml` 的 `POSTGRES_USER` 读取 |
| Password | 从 `compose.yaml` 的 `POSTGRES_PASSWORD` 读取 |

> 数据库名、用户名、密码一律从项目 `compose.yaml` 实际读取，不要臆测或使用示例值。

## 容器就绪判断

连接前先确认 db 容器已就绪：

```powershell
docker compose logs -f db
```

看到以下日志表示可连接：

```
database system is ready to accept connections
```

## 容器内 psql 验证

进入容器直接用 psql 连接（无需密码交互）：

```powershell
docker exec -it db-1 psql -U {POSTGRES_USER} -d {POSTGRES_DB}
```

把 `{POSTGRES_USER}` 与 `{POSTGRES_DB}` 替换为 compose.yaml 中的实际值。

## 验证 pgvector 扩展

连上后执行：

```sql
SELECT * FROM pg_extension WHERE extname='vector';
```

有返回行表示 vector 扩展已启用；无返回行表示扩展未创建，需检查数据库初始化脚本是否正确执行 `CREATE EXTENSION vector;`。

## 连不上的排查顺序

1. `scripts/pre-check.ps1` 看 5432 是否被宿主机本地 PostgreSQL 占用。
2. `docker compose ps` 确认 db-1 是否 running、端口映射是否正确。
3. `docker compose logs db` 看是否有初始化报错或崩溃重启。
4. 若映射为 5433，客户端端口要同步改为 5433。
5. 确认连接参数与 compose.yaml 完全一致（含大小写、特殊字符密码）。

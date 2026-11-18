#Requires -Version 5.1
<#
.SYNOPSIS
    PharmaMind-AI 部署前置检查：端口占用 + Docker 状态。
.DESCRIPTION
    检查 5432/8000/5173 端口是否被占用，并验证 Docker Daemon 是否正常。
    只读检查，不修改任何系统状态。建议在部署或排障的第一步运行。
#>

# 统一 UTF-8 输出，避免中文乱码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Stop'

function Write-Section {
    param([string]$Title)
    Write-Host "`n===== $Title =====" -ForegroundColor Cyan
}

Write-Section 'PharmaMind-AI 前置端口检查'

$ports = @(
    @{ Port = 5432; Note = 'pgvector 数据库 (PostgreSQL TCP)' },
    @{ Port = 8000; Note = 'FastAPI 后端' },
    @{ Port = 5173; Note = 'Vue 前端' }
)

$occupied = @()
foreach ($item in $ports) {
    $p = $item.Port
    Write-Host "检查端口 $p  ($($item.Note))"
    # 用 netstat 兼容所有 Windows 环境；同时用 Get-NetTCPConnection 交叉验证监听状态
    $res = netstat -ano | Select-String ":$p\s"
    $listening = $false
    try {
        $listening = [bool](Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue)
    } catch { }

    if ($res -or $listening) {
        Write-Host "  [WARN] 端口 $p 已被占用：" -ForegroundColor Yellow
        if ($res) { $res | ForEach-Object { Write-Host "    $($_.Line.Trim())" } }
        $occupied += $p

        if ($p -eq 5432) {
            Write-Host "  -> 5432 被占用：请二选一：" -ForegroundColor Yellow
            Write-Host "     (1) 停止宿主机本地 PostgreSQL 服务；"
            Write-Host '     (2) 将 compose.yaml 端口映射改为 "5433:5432"，客户端连接端口同步改为 5433。'
        }
    } else {
        Write-Host "  [OK] 端口 $p 空闲" -ForegroundColor Green
    }
}

Write-Section 'Docker 状态'
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Host '  [ERROR] 未找到 docker 命令，请确认 Docker Desktop 已安装并加入 PATH。' -ForegroundColor Red
    exit 1
}

& docker info 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host '  [ERROR] Docker Daemon 不可用，请重启 Docker Desktop 后重试。' -ForegroundColor Red
    exit 1
}
Write-Host '  [OK] Docker Daemon 正常' -ForegroundColor Green

Write-Section '结论'
if ($occupied.Count -gt 0) {
    Write-Host "  存在被占用端口：$($occupied -join ', ')。请按上方提示处理后继续。" -ForegroundColor Yellow
} else {
    Write-Host '  端口检查全部通过，可进入镜像源配置与预拉取流程。' -ForegroundColor Green
}

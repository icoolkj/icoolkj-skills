#Requires -Version 5.1
<#
.SYNOPSIS
    按顺序预拉取 PharmaMind-AI 的四个基础镜像，规避 compose 并发拉取导致的 429 限流。
.DESCRIPTION
    串行、逐个拉取 python/node/nginx/pgvector 基础镜像。任一步失败会明确提示并中止，
    避免带着不完整缓存进入 build 阶段。全部成功后才可运行 start.ps1。
#>

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Continue'

Write-Host '开始按顺序预拉取 PharmaMind-AI 基础镜像，规避 429 限流' -ForegroundColor Cyan

$images = @(
    'python:3.12-slim',
    'node:22-alpine',
    'nginx:1.27-alpine',
    'pgvector/pgvector:pg16'
)

$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Host '[ERROR] 未找到 docker 命令，请确认 Docker Desktop 已安装。' -ForegroundColor Red
    exit 1
}

$failed = @()
foreach ($img in $images) {
    Write-Host "`n--- 拉取 $img ---" -ForegroundColor Cyan
    & docker pull $img
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[WARN] $img 拉取失败，稍后重试（可等待 5~10 分钟规避限流）。" -ForegroundColor Yellow
        $failed += $img
    } else {
        Write-Host "[OK] $img 已就绪" -ForegroundColor Green
    }
}

Write-Host "`n===== 结果 =====" -ForegroundColor Cyan
if ($failed.Count -gt 0) {
    Write-Host "以下镜像拉取失败：$($failed -join ', ')" -ForegroundColor Red
    Write-Host '请等待数分钟后重新运行本脚本，全部成功后再执行 compose 构建。' -ForegroundColor Red
    exit 1
} else {
    Write-Host '[OK] 全部基础镜像已缓存，可以执行 start.ps1 进行构建启动。' -ForegroundColor Green
}

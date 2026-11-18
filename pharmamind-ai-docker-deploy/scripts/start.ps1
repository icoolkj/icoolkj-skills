#Requires -Version 5.1
<#
.SYNOPSIS
    一键重建并后台启动 PharmaMind-AI（docker compose down + up -d --build）。
.DESCRIPTION
    在 compose.yaml 所在目录执行：先停旧容器，再后台构建启动。
    可用 -Frontground 参数改为前台启动以实时观察日志；可用 -ComposeDir 指定项目目录。
.PARAMETER ComposeDir
    compose.yaml 所在目录，默认取当前目录。
.PARAMETER Frontground
    前台启动（不加 -d），便于观察构建与启动日志。
#>

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Stop'
param(
    [string]$ComposeDir = '.',
    [switch]$Frontground
)

$composePath = Join-Path $ComposeDir 'compose.yaml'
if (-not (Test-Path $composePath)) {
    # 兼容 docker-compose 老命名的 compose.yml / docker-compose.yml
    $alt = @('compose.yml', 'docker-compose.yml', 'docker-compose.yaml') |
        ForEach-Object { Join-Path $ComposeDir $_ } |
        Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($alt) { $composePath = $alt }
    else {
        Write-Host "[ERROR] 在 $ComposeDir 下未找到 compose.yaml，请用 -ComposeDir 指定正确目录。" -ForegroundColor Red
        exit 1
    }
}

Write-Host "使用 compose 文件：$composePath" -ForegroundColor Cyan
Push-Location (Split-Path $composePath -Parent)
try {
    Write-Host '===== 停止旧容器 =====' -ForegroundColor Cyan
    & docker compose down

    Write-Host '===== 构建并启动 =====' -ForegroundColor Cyan
    if ($Frontground) {
        & docker compose up --build
    } else {
        & docker compose up -d --build
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n服务启动完成（后台运行）" -ForegroundColor Green
            Write-Host '前端：      http://localhost:5173'
            Write-Host '后端接口：  http://localhost:8000'
            Write-Host '后端文档：  http://localhost:8000/docs'
            Write-Host '数据库：    localhost:5432 （请用数据库客户端连接，不要用浏览器）'
            Write-Host "`n查看实时日志请运行 logs-follow.ps1" -ForegroundColor Cyan
        } else {
            Write-Host '[ERROR] 构建/启动失败，请查看上方日志或运行 logs-follow.ps1 排查。' -ForegroundColor Red
            exit 1
        }
    }
} finally {
    Pop-Location
}

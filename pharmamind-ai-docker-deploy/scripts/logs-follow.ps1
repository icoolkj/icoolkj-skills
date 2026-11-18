#Requires -Version 5.1
<#
.SYNOPSIS
    实时跟踪 PharmaMind-AI 容器日志。
.DESCRIPTION
    不带参数跟踪全部容器；用 -Service 指定单个服务（frontend/backend/db）精准排查。
    就绪标志：db 看到 "database system is ready to accept connections"，
    backend 看到 "Application startup complete"。
.PARAMETER Service
    可选服务名：frontend / backend / db。
#>

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = 'Stop'
param(
    [ValidateSet('', 'frontend', 'backend', 'db')]
    [string]$Service = ''
)

if ($Service) {
    Write-Host "===== 实时日志：$Service （Ctrl+C 退出）=====" -ForegroundColor Cyan
    & docker compose logs -f $Service
} else {
    Write-Host '===== 实时日志：全部服务 （Ctrl+C 退出）=====' -ForegroundColor Cyan
    & docker compose logs -f
}

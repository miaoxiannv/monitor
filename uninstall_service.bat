@echo off
chcp 65001 >nul
echo ========================================
echo 进程监控服务 - 卸载系统服务
echo ========================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 请以管理员身份运行此脚本！
    pause
    exit /b 1
)

set "SERVICE_NAME=ProcessMonitor"

echo 即将卸载服务: %SERVICE_NAME%
echo.
set /p confirm="确认卸载? (Y/N): "

if /i not "%confirm%"=="Y" (
    echo 已取消
    pause
    exit /b 0
)

REM 停止服务
echo.
echo 正在停止服务...
nssm stop %SERVICE_NAME%
timeout /t 2 >nul

REM 删除服务
echo 正在删除服务...
nssm remove %SERVICE_NAME% confirm

echo.
echo ========================================
echo 卸载完成！
echo ========================================
pause

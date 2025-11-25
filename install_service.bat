@echo off
chcp 65001 >nul
echo ========================================
echo 进程监控服务 - 安装为Windows系统服务
echo ========================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 请以管理员身份运行此脚本！
    echo 右键点击文件 -^> 以管理员身份运行
    pause
    exit /b 1
)

REM 检查NSSM
where nssm >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到NSSM工具
    echo.
    echo 请下载NSSM: https://nssm.cc/download
    echo 1. 下载 nssm-2.24.zip
    echo 2. 解压后将 nssm.exe 复制到本目录
    echo 3. 或者将 nssm.exe 所在目录添加到系统PATH
    pause
    exit /b 1
)

REM 检查EXE文件
if not exist "ProcessMonitor.exe" (
    echo [错误] 未找到 ProcessMonitor.exe
    echo 请先运行 build.bat 打包程序
    pause
    exit /b 1
)

REM 获取当前目录
set "CURRENT_DIR=%cd%"
set "EXE_PATH=%CURRENT_DIR%\ProcessMonitor.exe"
set "SERVICE_NAME=ProcessMonitor"

echo 服务名称: %SERVICE_NAME%
echo 程序路径: %EXE_PATH%
echo 工作目录: %CURRENT_DIR%
echo.

REM 停止并删除已存在的服务
echo [1/3] 检查已存在的服务...
nssm status %SERVICE_NAME% >nul 2>&1
if %errorlevel% equ 0 (
    echo 发现已存在的服务，正在停止...
    nssm stop %SERVICE_NAME%
    timeout /t 2 >nul
    nssm remove %SERVICE_NAME% confirm
    echo 旧服务已删除
)

REM 安装服务
echo.
echo [2/3] 安装服务...
nssm install %SERVICE_NAME% "%EXE_PATH%"

REM 配置服务
echo.
echo [3/3] 配置服务...
nssm set %SERVICE_NAME% AppDirectory "%CURRENT_DIR%"
nssm set %SERVICE_NAME% DisplayName "进程监控服务"
nssm set %SERVICE_NAME% Description "监控指定进程并通过钉钉发送告警"
nssm set %SERVICE_NAME% Start SERVICE_AUTO_START
nssm set %SERVICE_NAME% AppStdout "%CURRENT_DIR%\logs\service_stdout.log"
nssm set %SERVICE_NAME% AppStderr "%CURRENT_DIR%\logs\service_stderr.log"

REM 启动服务
echo.
echo 正在启动服务...
nssm start %SERVICE_NAME%

timeout /t 2 >nul

REM 检查服务状态
nssm status %SERVICE_NAME%

echo.
echo ========================================
echo 安装完成！
echo.
echo 服务管理命令：
echo   查看状态: nssm status %SERVICE_NAME%
echo   启动服务: nssm start %SERVICE_NAME%
echo   停止服务: nssm stop %SERVICE_NAME%
echo   重启服务: nssm restart %SERVICE_NAME%
echo   卸载服务: nssm remove %SERVICE_NAME% confirm
echo.
echo Web管理界面: http://localhost:8080
echo 日志文件: %CURRENT_DIR%\logs\
echo.
echo ========================================
pause

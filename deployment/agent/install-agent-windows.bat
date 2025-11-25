@echo off
chcp 65001 >nul
echo ========================================
echo 进程监控Agent - Windows安装脚本
echo ========================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 请以管理员身份运行此脚本
    echo 右键点击文件 -> 以管理员身份运行
    pause
    exit /b 1
)

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 配置
set "INSTALL_DIR=%ProgramFiles%\MonitorAgent"
set "AGENT_PORT=8888"

echo [1/4] 安装Python依赖...
pip install flask psutil >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo [2/4] 创建安装目录...
mkdir "%INSTALL_DIR%" 2>nul
copy agent.py "%INSTALL_DIR%\" >nul
echo   已安装到: %INSTALL_DIR%

echo [3/4] 检查NSSM...
where nssm >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [警告] 未找到NSSM工具
    echo.
    echo 请下载NSSM: https://nssm.cc/download
    echo 1. 下载 nssm-2.24.zip
    echo 2. 解压后将 nssm.exe 复制到本目录
    echo 3. 重新运行此脚本
    echo.
    echo 或者手动运行Agent:
    echo   cd "%INSTALL_DIR%"
    echo   python agent.py
    pause
    exit /b 0
)

echo [4/4] 安装Windows服务...

REM 停止并删除已存在的服务
nssm status MonitorAgent >nul 2>&1
if %errorlevel% equ 0 (
    echo   发现已存在的服务，正在停止...
    nssm stop MonitorAgent
    timeout /t 2 >nul
    nssm remove MonitorAgent confirm
)

REM 安装服务
nssm install MonitorAgent python "%INSTALL_DIR%\agent.py"
nssm set MonitorAgent AppDirectory "%INSTALL_DIR%"
nssm set MonitorAgent DisplayName "进程监控Agent"
nssm set MonitorAgent Description "提供进程监控HTTP API"
nssm set MonitorAgent Start SERVICE_AUTO_START
nssm set MonitorAgent AppEnvironmentExtra AGENT_PORT=%AGENT_PORT%

REM 启动服务
echo   正在启动服务...
nssm start MonitorAgent
timeout /t 2 >nul

REM 检查服务状态
nssm status MonitorAgent

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo 服务名称: MonitorAgent
echo 监听端口: %AGENT_PORT%
echo.
echo 测试API:
echo   curl http://localhost:%AGENT_PORT%/api/health
echo   curl http://localhost:%AGENT_PORT%/api/processes
echo.
echo 服务管理:
echo   查看状态: nssm status MonitorAgent
echo   启动服务: nssm start MonitorAgent
echo   停止服务: nssm stop MonitorAgent
echo   重启服务: nssm restart MonitorAgent
echo.
echo 防火墙配置（如果需要远程访问）:
echo   netsh advfirewall firewall add rule name="MonitorAgent" dir=in action=allow protocol=TCP localport=%AGENT_PORT%
echo ========================================
pause

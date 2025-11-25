@echo off
chcp 65001 >nul
echo ========================================
echo 进程监控服务 - 打包为 EXE
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 安装依赖
echo [1/3] 安装依赖...
pip install -r requirements.txt
pip install pyinstaller

if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

REM 打包
echo.
echo [2/3] 打包为EXE...
pyinstaller --onefile ^
    --name ProcessMonitor ^
    --add-data "templates;templates" ^
    --hidden-import=engineio.async_drivers.threading ^
    --noconsole ^
    main.py

if %errorlevel% neq 0 (
    echo [错误] 打包失败
    pause
    exit /b 1
)

REM 复制配置文件
echo.
echo [3/3] 复制配置文件...
copy config.json dist\config.json

echo.
echo ========================================
echo 打包完成！
echo.
echo 输出目录: dist\ProcessMonitor.exe
echo 配置文件: dist\config.json
echo.
echo 下一步：
echo 1. 编辑 dist\config.json 配置钉钉Webhook
echo 2. 运行 install_service.bat 安装为系统服务
echo ========================================
pause

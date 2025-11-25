#!/bin/bash
# 主监控服务器安装脚本

set -e

echo "========================================="
echo "进程监控服务器 - 安装脚本"
echo "========================================="
echo

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    echo "错误: 请使用root权限运行此脚本"
    echo "使用: sudo bash install-server.sh"
    exit 1
fi

# 配置
INSTALL_DIR="/opt/monitor-server"
SERVICE_FILE="/etc/systemd/system/monitor-server.service"

# 1. 安装依赖
echo "[1/5] 安装Python依赖..."
pip3 install -r requirements.txt || {
    echo "错误: 无法安装依赖，请先安装pip3"
    exit 1
}

# 2. 创建用户
echo "[2/5] 创建monitor用户..."
if ! id "monitor" &>/dev/null; then
    useradd -r -s /bin/false monitor
    echo "  已创建用户: monitor"
else
    echo "  用户已存在: monitor"
fi

# 3. 安装文件
echo "[3/5] 安装服务文件..."
mkdir -p "$INSTALL_DIR"

# 复制所有必要的文件
cp main.py remote_monitor.py notifier.py heartbeat.py web.py "$INSTALL_DIR/"
cp -r templates "$INSTALL_DIR/"

# 复制配置文件（如果不存在）
if [ ! -f "$INSTALL_DIR/config.json" ]; then
    if [ -f "config.json" ]; then
        cp config.json "$INSTALL_DIR/"
    else
        cp config.example.json "$INSTALL_DIR/config.json"
        echo "  请编辑 $INSTALL_DIR/config.json 配置监控目标"
    fi
fi

# 创建logs目录
mkdir -p "$INSTALL_DIR/logs"

# 设置权限
chown -R monitor:monitor "$INSTALL_DIR"
echo "  已安装到: $INSTALL_DIR"

# 4. 安装systemd服务
echo "[4/5] 配置systemd服务..."
cp deployment/server/monitor-server.service "$SERVICE_FILE"
systemctl daemon-reload
echo "  服务文件: $SERVICE_FILE"

# 5. 启动服务
echo "[5/5] 启动服务..."
systemctl enable monitor-server
systemctl restart monitor-server

# 等待服务启动
sleep 3

# 检查状态
if systemctl is-active --quiet monitor-server; then
    WEB_PORT=$(grep -oP '"web_port":\s*\K\d+' "$INSTALL_DIR/config.json" || echo "8080")

    echo
    echo "========================================="
    echo "✅ 安装成功！"
    echo "========================================="
    echo "服务状态: 运行中"
    echo "Web界面: http://$(hostname -I | awk '{print $1}'):$WEB_PORT"
    echo "配置文件: $INSTALL_DIR/config.json"
    echo
    echo "管理命令:"
    echo "  查看状态: systemctl status monitor-server"
    echo "  查看日志: journalctl -u monitor-server -f"
    echo "  重启服务: systemctl restart monitor-server"
    echo "  停止服务: systemctl stop monitor-server"
    echo
    echo "下一步:"
    echo "  1. 编辑配置文件添加监控目标"
    echo "  2. 或访问Web界面在线配置"
    echo "  3. 重启服务使配置生效"
    echo "========================================="
else
    echo
    echo "❌ 服务启动失败"
    echo "查看日志: journalctl -u monitor-server -n 50"
    exit 1
fi

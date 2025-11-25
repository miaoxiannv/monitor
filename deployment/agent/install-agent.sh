#!/bin/bash
# Agent安装脚本 - 在被监控的Linux机器上运行

set -e

echo "========================================="
echo "进程监控Agent - 安装脚本"
echo "========================================="
echo

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    echo "错误: 请使用root权限运行此脚本"
    echo "使用: sudo bash install-agent.sh"
    exit 1
fi

# 配置
INSTALL_DIR="/opt/monitor-agent"
SERVICE_FILE="/etc/systemd/system/monitor-agent.service"
AGENT_PORT="${AGENT_PORT:-8888}"

# 1. 安装依赖
echo "[1/5] 安装Python依赖..."
pip3 install flask psutil >/dev/null 2>&1 || {
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
echo "[3/5] 安装Agent文件..."
mkdir -p "$INSTALL_DIR"
cp agent.py "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/agent.py"
chown -R monitor:monitor "$INSTALL_DIR"
echo "  已安装到: $INSTALL_DIR"

# 4. 安装systemd服务
echo "[4/5] 配置systemd服务..."
cp deployment/agent/monitor-agent.service "$SERVICE_FILE"
sed -i "s|AGENT_PORT=8888|AGENT_PORT=$AGENT_PORT|" "$SERVICE_FILE"
systemctl daemon-reload
echo "  服务文件: $SERVICE_FILE"

# 5. 启动服务
echo "[5/5] 启动服务..."
systemctl enable monitor-agent
systemctl restart monitor-agent

# 等待服务启动
sleep 2

# 检查状态
if systemctl is-active --quiet monitor-agent; then
    echo
    echo "========================================="
    echo "✅ 安装成功！"
    echo "========================================="
    echo "服务状态: 运行中"
    echo "监听端口: $AGENT_PORT"
    echo
    echo "测试API:"
    echo "  curl http://localhost:$AGENT_PORT/api/health"
    echo "  curl http://localhost:$AGENT_PORT/api/processes"
    echo
    echo "管理命令:"
    echo "  查看状态: systemctl status monitor-agent"
    echo "  查看日志: journalctl -u monitor-agent -f"
    echo "  重启服务: systemctl restart monitor-agent"
    echo "  停止服务: systemctl stop monitor-agent"
    echo
    echo "防火墙配置（如果需要）:"
    echo "  firewall-cmd --permanent --add-port=$AGENT_PORT/tcp"
    echo "  firewall-cmd --reload"
    echo "========================================="
else
    echo
    echo "❌ 服务启动失败"
    echo "查看日志: journalctl -u monitor-agent -n 50"
    exit 1
fi

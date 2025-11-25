"""
Web管理界面 - 支持多监控目标管理
"""
import json
import os
import logging
from flask import Flask, render_template, request, jsonify
from filelock import FileLock

logger = logging.getLogger(__name__)

# 全局变量（由main.py注入）
remote_monitor = None
notifier = None
heartbeat_monitor = None
CONFIG_FILE = "config.json"
CONFIG_LOCK = CONFIG_FILE + ".lock"


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False  # 支持中文

    @app.route('/')
    def index():
        """主页 - 显示监控目标状态"""
        status = get_status()
        return render_template('index.html', status=status)

    @app.route('/api/status')
    def api_status():
        """获取所有监控目标状态"""
        status = get_status()
        return jsonify(status)

    @app.route('/api/monitors', methods=['GET'])
    def get_monitors():
        """获取所有监控目标配置"""
        config = load_config()
        return jsonify({
            "success": True,
            "monitors": config.get("monitors", [])
        })

    @app.route('/api/monitors', methods=['POST'])
    def add_monitor():
        """添加新的监控目标"""
        try:
            new_monitor = request.json

            # 验证必填字段
            required_fields = ['name', 'host', 'port', 'processes']
            for field in required_fields:
                if field not in new_monitor:
                    return jsonify({
                        "success": False,
                        "error": f"缺少必填字段: {field}"
                    }), 400

            # 加载配置
            config = load_config()
            monitors = config.get("monitors", [])

            # 检查名称是否重复
            if any(m.get('name') == new_monitor['name'] for m in monitors):
                return jsonify({
                    "success": False,
                    "error": "监控目标名称已存在"
                }), 400

            # 添加默认值
            new_monitor.setdefault('enabled', True)
            new_monitor.setdefault('description', '')

            # 添加到配置
            monitors.append(new_monitor)
            config['monitors'] = monitors

            # 保存配置
            write_config(config)

            return jsonify({
                "success": True,
                "message": "监控目标已添加，重启服务后生效"
            })

        except Exception as e:
            logger.error(f"添加监控目标失败: {e}", exc_info=True)
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/monitors/<int:index>', methods=['PUT'])
    def update_monitor(index):
        """更新监控目标"""
        try:
            updated_monitor = request.json

            config = load_config()
            monitors = config.get("monitors", [])

            if index < 0 or index >= len(monitors):
                return jsonify({
                    "success": False,
                    "error": "监控目标不存在"
                }), 404

            # 更新配置
            monitors[index] = updated_monitor
            config['monitors'] = monitors
            write_config(config)

            return jsonify({
                "success": True,
                "message": "监控目标已更新，重启服务后生效"
            })

        except Exception as e:
            logger.error(f"更新监控目标失败: {e}", exc_info=True)
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/monitors/<int:index>', methods=['DELETE'])
    def delete_monitor(index):
        """删除监控目标"""
        try:
            config = load_config()
            monitors = config.get("monitors", [])

            if index < 0 or index >= len(monitors):
                return jsonify({
                    "success": False,
                    "error": "监控目标不存在"
                }), 404

            # 删除
            deleted = monitors.pop(index)
            config['monitors'] = monitors
            write_config(config)

            return jsonify({
                "success": True,
                "message": f"已删除监控目标: {deleted.get('name')}"
            })

        except Exception as e:
            logger.error(f"删除监控目标失败: {e}", exc_info=True)
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/config', methods=['GET'])
    def get_config():
        """获取完整配置"""
        config = load_config()
        # 隐藏敏感信息
        if 'notification' in config:
            if 'dingtalk_secret' in config['notification']:
                config['notification']['dingtalk_secret'] = '***'
        return jsonify(config)

    @app.route('/api/config', methods=['POST'])
    def save_config():
        """保存完整配置"""
        try:
            new_config = request.json

            # 简单验证
            if 'monitors' not in new_config:
                return jsonify({
                    "success": False,
                    "error": "配置格式错误"
                }), 400

            write_config(new_config)

            return jsonify({
                "success": True,
                "message": "配置已保存，重启服务后生效"
            })

        except Exception as e:
            logger.error(f"保存配置失败: {e}", exc_info=True)
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/test-agent', methods=['POST'])
    def test_agent():
        """测试Agent连接"""
        try:
            data = request.json
            host = data.get('host')
            port = data.get('port', 8888)

            if not host:
                return jsonify({
                    "success": False,
                    "error": "请提供主机地址"
                }), 400

            if remote_monitor is None:
                return jsonify({
                    "success": False,
                    "error": "监控器未初始化"
                }), 500

            # 测试连接
            health = remote_monitor.check_agent_health(host, port, timeout=5)

            if health:
                return jsonify({
                    "success": True,
                    "message": "Agent连接成功",
                    "data": health
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "无法连接到Agent，请检查地址和端口"
                }), 500

        except Exception as e:
            logger.error(f"测试Agent连接失败: {e}", exc_info=True)
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/test-notification', methods=['POST'])
    def test_notification():
        """测试钉钉通知"""
        try:
            if notifier is None:
                return jsonify({"success": False, "error": "通知器未初始化"}), 500

            success = notifier.send_test_message()

            if success:
                return jsonify({"success": True, "message": "测试消息已发送"})
            else:
                return jsonify({
                    "success": False,
                    "error": "发送失败，请检查配置"
                }), 500

        except Exception as e:
            logger.error(f"测试通知失败: {e}", exc_info=True)
            return jsonify({"success": False, "error": str(e)}), 500

    return app


def load_config():
    """加载配置（带文件锁）"""
    lock = FileLock(CONFIG_LOCK)
    try:
        with lock.acquire(timeout=5):
            if not os.path.exists(CONFIG_FILE):
                return {}
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"加载配置失败: {e}")
        return {}


def write_config(config):
    """写入配置（带文件锁）"""
    lock = FileLock(CONFIG_LOCK)
    with lock.acquire(timeout=5):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)


def get_status():
    """获取当前监控状态"""
    if remote_monitor is None:
        return {"error": "监控器未初始化"}

    return {
        "monitors": remote_monitor.get_all_status(),
        "heartbeat_enabled": heartbeat_monitor.enabled if heartbeat_monitor else False
    }


def set_monitor_instances(rm, nf, hb):
    """设置监控器实例（由main.py调用）"""
    global remote_monitor, notifier, heartbeat_monitor
    remote_monitor = rm
    notifier = nf
    heartbeat_monitor = hb

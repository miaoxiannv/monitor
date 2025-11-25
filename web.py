"""
Web管理界面 - 简洁的Flask实现
"""
import json
import os
import logging
from flask import Flask, render_template, request, jsonify
from filelock import FileLock

logger = logging.getLogger(__name__)

# 全局变量（由main.py注入）
process_monitor = None
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
        """主页 - 显示配置和状态"""
        config = load_config()
        status = get_status()
        return render_template('index.html', config=config, status=status)

    @app.route('/api/config', methods=['GET'])
    def get_config():
        """获取配置"""
        config = load_config()
        return jsonify(config)

    @app.route('/api/config', methods=['POST'])
    def save_config():
        """保存配置"""
        try:
            new_config = request.json

            # 简单验证
            if not isinstance(new_config.get('processes'), list):
                return jsonify({"success": False, "error": "processes必须是数组"}), 400

            if not isinstance(new_config.get('check_interval'), int):
                return jsonify({"success": False, "error": "check_interval必须是整数"}), 400

            # 保存配置
            write_config(new_config)

            return jsonify({
                "success": True,
                "message": "配置已保存，重启服务后生效"
            })

        except Exception as e:
            logger.error(f"保存配置失败: {e}", exc_info=True)
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/status')
    def api_status():
        """获取当前状态"""
        status = get_status()
        return jsonify(status)

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
                return jsonify({"success": False, "error": "发送失败，请检查配置"}), 500

        except Exception as e:
            logger.error(f"测试通知失败: {e}", exc_info=True)
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/check-now', methods=['POST'])
    def check_now():
        """立即执行一次进程检查"""
        try:
            if process_monitor is None:
                return jsonify({"success": False, "error": "监控器未初始化"}), 500

            process_monitor.check_processes()
            return jsonify({"success": True, "message": "检查已执行"})

        except Exception as e:
            logger.error(f"立即检查失败: {e}", exc_info=True)
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
    if process_monitor is None:
        return {"error": "监控器未初始化"}

    return {
        "processes": process_monitor.get_current_status(),
        "heartbeat_enabled": heartbeat_monitor.enabled if heartbeat_monitor else False
    }


def set_monitor_instances(pm, nf, hb):
    """设置监控器实例（由main.py调用）"""
    global process_monitor, notifier, heartbeat_monitor
    process_monitor = pm
    notifier = nf
    heartbeat_monitor = hb

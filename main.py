"""
进程监控服务 - 主入口
启动三个线程：进程监控、心跳监控、Web界面
"""
import json
import os
import sys
import logging
import signal
import threading
from logging.handlers import RotatingFileHandler

from monitor import create_process_monitor
from notifier import create_notifier
from heartbeat import create_heartbeat_monitor
from web import create_app, set_monitor_instances

# 配置文件路径
CONFIG_FILE = "config.json"


def setup_logging():
    """配置日志系统"""
    # 创建logs目录
    os.makedirs("logs", exist_ok=True)

    # 配置根日志器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 文件输出（滚动日志，最多保留5个文件，每个10MB）
    file_handler = RotatingFileHandler(
        'logs/monitor.log',
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(console_formatter)
    logger.addHandler(file_handler)


def load_config():
    """加载配置文件"""
    if not os.path.exists(CONFIG_FILE):
        logging.error(f"配置文件不存在: {CONFIG_FILE}")
        sys.exit(1)

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logging.info("配置文件加载成功")
            return config
    except Exception as e:
        logging.error(f"加载配置文件失败: {e}")
        sys.exit(1)


class MonitorService:
    """监控服务主类"""

    def __init__(self):
        self.config = None
        self.notifier = None
        self.process_monitor = None
        self.heartbeat_monitor = None
        self.threads = []
        self.stop_event = threading.Event()

    def initialize(self):
        """初始化服务"""
        logging.info("=" * 50)
        logging.info("进程监控服务启动中...")
        logging.info("=" * 50)

        # 加载配置
        self.config = load_config()

        # 创建组件
        self.notifier = create_notifier(self.config)
        self.process_monitor = create_process_monitor(self.config, self.notifier)
        self.heartbeat_monitor = create_heartbeat_monitor(self.config)

        # 注入到web模块
        set_monitor_instances(
            self.process_monitor,
            self.notifier,
            self.heartbeat_monitor
        )

        logging.info("服务组件初始化完成")

    def start(self):
        """启动所有线程"""
        # 发送启动通知
        self.notifier.send_startup_notification()

        # 启动进程监控线程
        monitor_thread = threading.Thread(
            target=self.process_monitor.run,
            name="ProcessMonitor",
            daemon=True
        )
        monitor_thread.start()
        self.threads.append(monitor_thread)
        logging.info("进程监控线程已启动")

        # 启动心跳监控线程
        heartbeat_thread = threading.Thread(
            target=self.heartbeat_monitor.run,
            name="HeartbeatMonitor",
            daemon=True
        )
        heartbeat_thread.start()
        self.threads.append(heartbeat_thread)
        logging.info("心跳监控线程已启动")

        # 启动Web服务（在主线程）
        web_host = self.config.get("web_host", "127.0.0.1")
        web_port = self.config.get("web_port", 8080)

        logging.info(f"Web管理界面: http://{web_host}:{web_port}")
        logging.info("=" * 50)
        logging.info("服务启动完成！")
        logging.info("按 Ctrl+C 停止服务")
        logging.info("=" * 50)

        app = create_app()

        # 启动Flask（关闭调试模式，避免重载）
        app.run(
            host=web_host,
            port=web_port,
            debug=False,
            use_reloader=False
        )

    def stop(self):
        """停止服务"""
        logging.info("正在停止服务...")

        # 停止监控器
        self.process_monitor.stop()
        self.heartbeat_monitor.stop()

        # 等待线程退出
        for thread in self.threads:
            thread.join(timeout=5)

        logging.info("服务已停止")

    def signal_handler(self, signum, frame):
        """处理系统信号"""
        logging.info(f"收到停止信号 ({signum})")
        self.stop()
        sys.exit(0)


def main():
    """主函数"""
    # 设置日志
    setup_logging()

    # 创建服务
    service = MonitorService()

    # 注册信号处理（Windows支持SIGINT，Linux支持SIGTERM）
    signal.signal(signal.SIGINT, service.signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, service.signal_handler)

    try:
        # 初始化并启动
        service.initialize()
        service.start()

    except KeyboardInterrupt:
        logging.info("收到键盘中断信号")
        service.stop()

    except Exception as e:
        logging.error(f"服务异常退出: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

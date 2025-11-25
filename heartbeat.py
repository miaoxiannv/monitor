"""
心跳监控模块 - 防止服务自身死机
使用 Healthchecks.io 实现外部监控
"""
import requests
import time
import logging
import threading

logger = logging.getLogger(__name__)


class HeartbeatMonitor:
    """心跳监控器"""

    def __init__(self, config):
        self.enabled = config.get("heartbeat", {}).get("enabled", False)
        self.url = config.get("heartbeat", {}).get("url", "")
        self.interval = config.get("heartbeat", {}).get("interval", 30)
        self._stop_event = threading.Event()

    def send_heartbeat(self):
        """发送单次心跳"""
        if not self.enabled:
            return False

        if not self.url or "YOUR_UUID_HERE" in self.url:
            logger.warning("Healthchecks.io URL未配置，心跳功能未启用")
            return False

        try:
            response = requests.get(self.url, timeout=10)
            if response.status_code == 200:
                logger.debug("心跳发送成功")
                return True
            else:
                logger.warning(f"心跳发送失败: HTTP {response.status_code}")
                return False

        except requests.RequestException as e:
            logger.error(f"心跳发送异常: {e}")
            return False

    def send_heartbeat_start(self):
        """发送启动信号"""
        if not self.enabled or not self.url:
            return

        try:
            # Healthchecks.io 支持 /start 端点记录任务开始
            start_url = self.url.rstrip('/') + '/start'
            requests.get(start_url, timeout=10)
            logger.info("发送启动心跳信号")
        except Exception as e:
            logger.error(f"发送启动心跳失败: {e}")

    def send_heartbeat_fail(self, message=""):
        """发送失败信号"""
        if not self.enabled or not self.url:
            return

        try:
            # Healthchecks.io 支持 /fail 端点记录失败
            fail_url = self.url.rstrip('/') + '/fail'
            requests.post(fail_url, data=message.encode('utf-8'), timeout=10)
            logger.info(f"发送失败心跳信号: {message}")
        except Exception as e:
            logger.error(f"发送失败心跳失败: {e}")

    def run(self):
        """心跳循环（在独立线程中运行）"""
        if not self.enabled:
            logger.info("心跳监控未启用")
            return

        logger.info(f"心跳监控已启动，间隔 {self.interval} 秒")
        self.send_heartbeat_start()

        while not self._stop_event.is_set():
            self.send_heartbeat()
            # 使用wait代替sleep，便于快速退出
            self._stop_event.wait(timeout=self.interval)

        logger.info("心跳监控已停止")

    def stop(self):
        """停止心跳"""
        self._stop_event.set()


def create_heartbeat_monitor(config):
    """从配置创建心跳监控器"""
    return HeartbeatMonitor(config)

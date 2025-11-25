"""
钉钉通知模块 - 简单可靠的推送实现
"""
import requests
import socket
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DingTalkNotifier:
    """钉钉机器人通知器"""

    def __init__(self, webhook_url):
        self.webhook_url = webhook_url
        self.hostname = socket.gethostname()

    def send(self, message, retry=3):
        """
        发送钉钉通知

        Args:
            message: 消息内容
            retry: 重试次数（默认3次）

        Returns:
            bool: 发送是否成功
        """
        if not self.webhook_url or "YOUR_ACCESS_TOKEN_HERE" in self.webhook_url:
            logger.warning("钉钉Webhook未配置，跳过发送")
            return False

        payload = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }

        for attempt in range(retry):
            try:
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("errcode") == 0:
                        logger.info(f"钉钉通知发送成功: {message[:50]}...")
                        return True
                    else:
                        logger.error(f"钉钉API返回错误: {result}")
                else:
                    logger.error(f"钉钉请求失败: HTTP {response.status_code}")

            except requests.RequestException as e:
                logger.error(f"钉钉发送异常 (尝试 {attempt + 1}/{retry}): {e}")

            if attempt < retry - 1:
                time.sleep(5)  # 重试前等待5秒

        return False

    def send_process_alert(self, process_name, status="stopped"):
        """发送进程告警"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"""【进程告警】
主机: {self.hostname}
进程: {process_name}
状态: {status}
时间: {timestamp}"""

        return self.send(message)

    def send_startup_notification(self):
        """发送服务启动通知"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"""【监控服务启动】
主机: {self.hostname}
状态: 服务已启动
时间: {timestamp}"""

        return self.send(message)

    def send_test_message(self):
        """发送测试消息"""
        message = f"""【测试消息】
主机: {self.hostname}
状态: 钉钉通知配置正常
时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""

        return self.send(message)


def create_notifier(config):
    """从配置创建通知器"""
    webhook = config.get("notification", {}).get("dingtalk_webhook", "")
    return DingTalkNotifier(webhook)

"""
钉钉通知模块 - 简单可靠的推送实现
支持加签安全设置
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import socket
import time
import hmac
import hashlib
import base64
import urllib.parse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DingTalkNotifier:
    """钉钉机器人通知器"""

    def __init__(self, webhook_url, secret=None):
        self.webhook_url = webhook_url
        self.secret = secret  # 加签密钥
        self.hostname = socket.gethostname()
        # 创建带重试策略的Session
        self.session = self._create_session()

    def _create_session(self):
        """创建增强的HTTP会话"""
        session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,  # 1秒、2秒、4秒递增
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=1,
            pool_maxsize=1
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # 设置默认请求头
        session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Connection': 'close'  # 不使用keep-alive，避免连接复用问题
        })

        return session

    def _get_signed_url(self):
        """
        生成带签名的Webhook URL（如果配置了secret）

        钉钉加签算法：
        1. timestamp = 当前时间戳（毫秒）
        2. string_to_sign = timestamp + "\n" + secret
        3. hmac_code = HmacSHA256(string_to_sign, secret)
        4. sign = Base64(hmac_code)
        5. url = webhook + "&timestamp=" + timestamp + "&sign=" + urlEncode(sign)
        """
        if not self.secret:
            # 没有配置secret，直接返回原始URL
            return self.webhook_url

        # 当前时间戳（毫秒）
        timestamp = str(round(time.time() * 1000))

        # 构造签名字符串
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')

        # 使用HmacSHA256算法计算签名
        hmac_code = hmac.new(
            secret_enc,
            string_to_sign_enc,
            digestmod=hashlib.sha256
        ).digest()

        # Base64编码
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

        # 构造最终URL
        signed_url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"

        logger.debug(f"生成签名URL: timestamp={timestamp}")
        return signed_url

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
                # 获取签名URL（如果配置了secret）
                url = self._get_signed_url()

                response = self.session.post(
                    url,  # 使用签名URL
                    json=payload,
                    timeout=(5, 10),  # (连接超时, 读取超时)
                    verify=True  # 验证SSL证书
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

            except requests.exceptions.SSLError as e:
                logger.error(f"SSL证书验证失败 (尝试 {attempt + 1}/{retry}): {e}")
                logger.warning("提示: 如果在企业网络环境，可能需要配置代理或信任证书")

            except requests.exceptions.ConnectionError as e:
                logger.error(f"连接错误 (尝试 {attempt + 1}/{retry}): {e}")
                logger.warning("提示: 检查网络连接或防火墙设置")

            except requests.exceptions.Timeout as e:
                logger.error(f"请求超时 (尝试 {attempt + 1}/{retry}): {e}")

            except requests.RequestException as e:
                logger.error(f"钉钉发送异常 (尝试 {attempt + 1}/{retry}): {e}")

            if attempt < retry - 1:
                wait_time = (attempt + 1) * 3  # 递增等待: 3秒、6秒、9秒
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)

        logger.error("钉钉通知发送失败，已达到最大重试次数")
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
    notification_config = config.get("notification", {})
    webhook = notification_config.get("dingtalk_webhook", "")
    secret = notification_config.get("dingtalk_secret", "")  # 读取加签密钥
    return DingTalkNotifier(webhook, secret)

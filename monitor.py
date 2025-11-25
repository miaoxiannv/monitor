"""
进程监控核心模块 - 简单的状态机实现
"""
import psutil
import time
import logging
import threading
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class ProcessMonitor:
    """进程监控器"""

    def __init__(self, config, notifier):
        self.config = config
        self.notifier = notifier
        self.last_state = {}  # 进程上次的运行状态
        self.last_alert_time = defaultdict(float)  # 上次告警时间（用于冷却）
        self._stop_event = threading.Event()

    def is_process_running(self, process_name):
        """
        检查进程是否在运行

        Args:
            process_name: 进程名（如 "notepad.exe"）

        Returns:
            bool: 是否在运行
        """
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() == process_name.lower():
                    return True
            return False
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def check_processes(self):
        """检查所有配置的进程"""
        processes = self.config.get("processes", [])
        current_state = {}

        for process_name in processes:
            is_running = self.is_process_running(process_name)
            current_state[process_name] = is_running

            # 状态机逻辑
            was_running = self.last_state.get(process_name, None)

            if was_running is None:
                # 首次检测，只记录状态
                logger.info(f"开始监控进程: {process_name} (当前状态: {'运行' if is_running else '未运行'})")

            elif was_running and not is_running:
                # 进程从运行变为停止 - 发送告警
                self._send_alert_with_cooldown(process_name)

            elif not was_running and is_running:
                # 进程从停止变为运行 - 记录日志
                logger.info(f"进程已恢复运行: {process_name}")

        self.last_state = current_state

    def _send_alert_with_cooldown(self, process_name):
        """带冷却期的告警发送"""
        now = time.time()
        cooldown = self.config.get("alert_cooldown", 300)
        last_alert = self.last_alert_time[process_name]

        if now - last_alert >= cooldown:
            logger.warning(f"检测到进程停止: {process_name}")
            if self.notifier.send_process_alert(process_name, "已停止"):
                self.last_alert_time[process_name] = now
            else:
                logger.error(f"告警发送失败: {process_name}")
        else:
            remaining = int(cooldown - (now - last_alert))
            logger.debug(f"进程 {process_name} 在冷却期内，跳过告警 (剩余 {remaining} 秒)")

    def get_current_status(self):
        """获取当前所有进程的状态"""
        processes = self.config.get("processes", [])
        status = []

        for process_name in processes:
            is_running = self.is_process_running(process_name)
            last_alert = self.last_alert_time.get(process_name, 0)

            status.append({
                "name": process_name,
                "running": is_running,
                "last_alert": datetime.fromtimestamp(last_alert).strftime("%Y-%m-%d %H:%M:%S") if last_alert > 0 else "从未告警"
            })

        return status

    def run(self):
        """监控循环（在独立线程中运行）"""
        check_interval = self.config.get("check_interval", 30)
        logger.info(f"进程监控已启动，检查间隔 {check_interval} 秒")

        while not self._stop_event.is_set():
            try:
                self.check_processes()
            except Exception as e:
                logger.error(f"进程检查异常: {e}", exc_info=True)

            # 使用wait代替sleep，便于快速退出
            self._stop_event.wait(timeout=check_interval)

        logger.info("进程监控已停止")

    def stop(self):
        """停止监控"""
        self._stop_event.set()


def create_process_monitor(config, notifier):
    """从配置创建进程监控器"""
    return ProcessMonitor(config, notifier)

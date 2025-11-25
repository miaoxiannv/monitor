"""
进程监控核心模块 - 远程Agent监控实现
通过HTTP请求各个Agent获取进程状态
"""
import requests
import time
import logging
import threading
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class RemoteMonitor:
    """远程监控器 - 通过HTTP监控远程Agent"""

    def __init__(self, config, notifier):
        self.config = config
        self.notifier = notifier
        self.monitors = config.get("monitors", [])
        self.last_state = {}  # {monitor_name: {process: running}}
        self.last_alert_time = defaultdict(float)  # 上次告警时间
        self._stop_event = threading.Event()

    def check_agent_health(self, host, port, timeout=5):
        """
        检查Agent健康状态

        Returns:
            dict: {"status": "ok", "hostname": "..."}
            None: 连接失败
        """
        try:
            url = f"http://{host}:{port}/api/health"
            response = requests.get(url, timeout=timeout)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Agent健康检查失败 {host}:{port} - HTTP {response.status_code}")
                return None

        except requests.RequestException as e:
            logger.error(f"Agent连接失败 {host}:{port} - {e}")
            return None

    def get_remote_processes(self, host, port, timeout=10):
        """
        获取远程Agent的进程列表

        Returns:
            list: 进程名列表
            None: 获取失败
        """
        try:
            url = f"http://{host}:{port}/api/processes"
            response = requests.get(url, timeout=timeout)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    return data.get("processes", [])
                else:
                    logger.error(f"Agent返回错误: {data}")
                    return None
            else:
                logger.error(f"获取进程列表失败 {host}:{port} - HTTP {response.status_code}")
                return None

        except requests.RequestException as e:
            logger.error(f"请求Agent失败 {host}:{port} - {e}")
            return None

    def is_process_running(self, process_name, running_processes):
        """
        检查进程是否在运行进程列表中

        Args:
            process_name: 进程名
            running_processes: 当前运行的进程列表

        Returns:
            bool: 是否运行
        """
        if not running_processes:
            return False
        return process_name in running_processes

    def check_monitor(self, monitor):
        """检查单个监控目标"""
        monitor_name = monitor.get("name", "未命名")
        host = monitor.get("host")
        port = monitor.get("port", 8888)
        processes_to_monitor = monitor.get("processes", [])

        logger.debug(f"检查监控目标: {monitor_name} ({host}:{port})")

        # 获取远程进程列表
        running_processes = self.get_remote_processes(host, port)

        if running_processes is None:
            # Agent连接失败
            logger.warning(f"监控目标离线: {monitor_name} ({host}:{port})")
            # TODO: 可以发送"监控目标离线"告警
            return

        # 检查每个需要监控的进程
        current_state = {}
        for process_name in processes_to_monitor:
            is_running = self.is_process_running(process_name, running_processes)
            current_state[process_name] = is_running

            # 状态机逻辑
            monitor_key = f"{monitor_name}:{process_name}"
            was_running = self.last_state.get(monitor_key, None)

            if was_running is None:
                # 首次检测
                logger.info(f"开始监控 [{monitor_name}] {process_name} (当前: {'运行' if is_running else '未运行'})")

            elif was_running and not is_running:
                # 进程从运行变为停止 - 发送告警
                self._send_alert_with_cooldown(monitor_name, host, process_name)

            elif not was_running and is_running:
                # 进程从停止变为运行
                logger.info(f"进程已恢复 [{monitor_name}] {process_name}")

            self.last_state[monitor_key] = is_running

    def _send_alert_with_cooldown(self, monitor_name, host, process_name):
        """带冷却期的告警发送"""
        now = time.time()
        cooldown = self.config.get("alert_cooldown", 300)
        alert_key = f"{monitor_name}:{process_name}"
        last_alert = self.last_alert_time[alert_key]

        if now - last_alert >= cooldown:
            logger.warning(f"检测到进程停止 [{monitor_name}] {process_name}")

            # 发送告警
            success = self.notifier.send_process_alert_remote(
                monitor_name,
                host,
                process_name,
                "已停止"
            )

            if success:
                self.last_alert_time[alert_key] = now
            else:
                logger.error(f"告警发送失败: [{monitor_name}] {process_name}")
        else:
            remaining = int(cooldown - (now - last_alert))
            logger.debug(f"进程 [{monitor_name}] {process_name} 在冷却期内，跳过告警 (剩余 {remaining} 秒)")

    def check_all_monitors(self):
        """检查所有启用的监控目标"""
        active_monitors = [m for m in self.monitors if m.get("enabled", True)]

        if not active_monitors:
            logger.warning("没有启用的监控目标")
            return

        logger.info(f"开始检查 {len(active_monitors)} 个监控目标...")

        for monitor in active_monitors:
            try:
                self.check_monitor(monitor)
            except Exception as e:
                monitor_name = monitor.get("name", "未命名")
                logger.error(f"检查监控目标失败 [{monitor_name}]: {e}", exc_info=True)

    def get_all_status(self):
        """获取所有监控目标的状态"""
        status_list = []

        for monitor in self.monitors:
            monitor_name = monitor.get("name", "未命名")
            host = monitor.get("host")
            port = monitor.get("port", 8888)
            enabled = monitor.get("enabled", True)
            processes = monitor.get("processes", [])

            # 检查Agent健康状态
            if enabled:
                health = self.check_agent_health(host, port, timeout=3)
                agent_status = "在线" if health else "离线"
                agent_hostname = health.get("hostname", "unknown") if health else "unknown"
            else:
                agent_status = "已禁用"
                agent_hostname = "unknown"

            # 获取每个进程的状态
            process_status = []
            for proc in processes:
                monitor_key = f"{monitor_name}:{proc}"
                is_running = self.last_state.get(monitor_key, None)
                last_alert = self.last_alert_time.get(monitor_key, 0)

                process_status.append({
                    "name": proc,
                    "running": is_running,
                    "last_alert": datetime.fromtimestamp(last_alert).strftime("%Y-%m-%d %H:%M:%S") if last_alert > 0 else "从未告警"
                })

            status_list.append({
                "monitor_name": monitor_name,
                "host": host,
                "port": port,
                "enabled": enabled,
                "agent_status": agent_status,
                "agent_hostname": agent_hostname,
                "processes": process_status,
                "description": monitor.get("description", "")
            })

        return status_list

    def run(self):
        """监控循环（在独立线程中运行）"""
        check_interval = self.config.get("check_interval", 30)
        logger.info(f"远程监控已启动，检查间隔 {check_interval} 秒")

        while not self._stop_event.is_set():
            try:
                self.check_all_monitors()
            except Exception as e:
                logger.error(f"监控检查异常: {e}", exc_info=True)

            # 使用wait代替sleep，便于快速退出
            self._stop_event.wait(timeout=check_interval)

        logger.info("远程监控已停止")

    def stop(self):
        """停止监控"""
        self._stop_event.set()


def create_remote_monitor(config, notifier):
    """从配置创建远程监控器"""
    return RemoteMonitor(config, notifier)

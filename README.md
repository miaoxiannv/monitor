# Windows 进程监控服务

一个简单可靠的Windows进程监控工具，当指定进程停止时通过钉钉发送实时告警到手机。

## 核心特性

- ✅ **进程监控** - 实时监控指定的Windows进程，检测进程停止事件
- ✅ **钉钉推送** - 通过钉钉机器人即时推送告警到手机（<1秒延迟）
- ✅ **心跳监控** - 集成Healthchecks.io，防止监控服务自身死机
- ✅ **Web管理** - 简洁的Web界面管理配置，无需手动编辑配置文件
- ✅ **系统服务** - 注册为Windows系统服务，开机自启，持续运行
- ✅ **告警冷却** - 避免频繁告警骚扰，同一进程5分钟内只告警一次

## 快速开始

### 环境要求

- Windows 7/10/11
- Python 3.7+ （仅开发/打包时需要）

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置钉钉机器人

1. 打开钉钉群 → **群设置** → **智能群助手** → **添加机器人** → **自定义**
2. 设置机器人名称（如"进程监控"），获取 **Webhook URL**
3. 复制Webhook URL（格式：`https://oapi.dingtalk.com/robot/send?access_token=xxx`）

### 3. （可选）配置心跳监控

1. 访问 [Healthchecks.io](https://healthchecks.io/)
2. 创建账号并添加新的监控项
3. 设置检查周期为 **1分钟**
4. 复制 **Ping URL**（格式：`https://hc-ping.com/your-uuid-here`）

### 4. 配置文件设置

**首次使用需要创建配置文件：**

```bash
# 复制示例配置
cp config.example.json config.json
```

然后编辑 `config.json` 填入你的配置：

```json
{
  "processes": [
    "notepad.exe",
    "chrome.exe"
  ],
  "notification": {
    "dingtalk_webhook": "你的钉钉Webhook URL",
    "dingtalk_secret": "你的Secret密钥（如果使用加签）"
  },
  "heartbeat": {
    "enabled": true,
    "url": "你的Healthchecks.io URL",
    "interval": 30
  },
  "check_interval": 30,
  "alert_cooldown": 300,
  "web_port": 8080,
  "web_host": "127.0.0.1"
}
```

**钉钉配置说明：**
- **使用加签**：需要配置 `dingtalk_secret`（以SEC开头）
- **使用关键词/IP白名单**：不需要配置 `dingtalk_secret`

详细配置指南请查看：[DINGTALK_SETUP.md](DINGTALK_SETUP.md)

⚠️ **重要：** `config.json` 包含敏感信息，已被 `.gitignore` 忽略，不会提交到 Git

### 5. 测试运行

```bash
python main.py
```

访问 http://localhost:8080 查看Web管理界面。

## 部署为系统服务

### 方法一：使用打包脚本（推荐）

#### 1. 打包为EXE

```bash
build.bat
```

打包完成后会生成：
- `dist/ProcessMonitor.exe` - 可执行文件
- `dist/config.json` - 配置文件

#### 2. 下载NSSM

NSSM (Non-Sucking Service Manager) 是一个轻量级的Windows服务管理工具。

- 官网：https://nssm.cc/download
- 下载 `nssm-2.24.zip`
- 解压后将 `nssm.exe`（根据系统选择32位或64位）复制到 `dist/` 目录

#### 3. 安装服务

**以管理员身份**运行：

```bash
cd dist
install_service.bat
```

服务会自动启动，访问 http://localhost:8080 管理配置。

### 方法二：手动安装（开发环境）

适用于直接运行Python脚本：

```bash
nssm install ProcessMonitor "C:\Python39\python.exe" "C:\path\to\monitor\main.py"
nssm set ProcessMonitor AppDirectory "C:\path\to\monitor"
nssm set ProcessMonitor Start SERVICE_AUTO_START
nssm start ProcessMonitor
```

## 服务管理

### 查看服务状态

```bash
nssm status ProcessMonitor
```

### 启动/停止/重启

```bash
nssm start ProcessMonitor
nssm stop ProcessMonitor
nssm restart ProcessMonitor
```

### 卸载服务

**以管理员身份**运行：

```bash
uninstall_service.bat
```

或手动卸载：

```bash
nssm stop ProcessMonitor
nssm remove ProcessMonitor confirm
```

## Web管理界面

访问 http://localhost:8080

功能：
- 📊 **实时状态** - 查看所有进程的运行状态
- ⚙️ **配置管理** - 可视化编辑配置
- 📱 **测试通知** - 测试钉钉推送是否正常
- 🔄 **立即检测** - 手动触发一次进程检查

⚠️ **注意：** 修改配置后需要重启服务才能生效

```bash
nssm restart ProcessMonitor
```

## 配置说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `processes` | 要监控的进程列表（数组） | `[]` |
| `dingtalk_webhook` | 钉钉机器人Webhook URL | - |
| `heartbeat.enabled` | 是否启用心跳监控 | `false` |
| `heartbeat.url` | Healthchecks.io Ping URL | - |
| `heartbeat.interval` | 心跳发送间隔（秒） | `30` |
| `check_interval` | 进程检查间隔（秒） | `30` |
| `alert_cooldown` | 告警冷却期（秒） | `300` |
| `web_port` | Web界面端口 | `8080` |
| `web_host` | Web界面监听地址 | `127.0.0.1` |

## 告警消息示例

### 进程停止告警

```
【进程告警】
主机: DESKTOP-ABC123
进程: chrome.exe
状态: 已停止
时间: 2025-01-15 14:32:05
```

### 服务启动通知

```
【监控服务启动】
主机: DESKTOP-ABC123
状态: 服务已启动
时间: 2025-01-15 14:30:00
```

### 死机告警（由Healthchecks.io发送）

```
DESKTOP-ABC123 is DOWN
Last ping was 2 minutes ago
```

## 常见问题

### 1. 如何监控特定路径的进程？

目前只支持进程名匹配。如果需要监控特定路径的进程，建议监控进程名并结合其他监控工具。

### 2. 可以监控多少个进程？

理论上无限制，但建议不超过20个进程，以免影响性能。

### 3. 告警延迟有多大？

- **进程停止检测延迟** = `check_interval`（默认30秒）
- **钉钉推送延迟** < 1秒
- **总延迟** ≈ 30秒

### 4. 如何处理频繁重启的进程？

增加 `alert_cooldown` 参数（默认300秒），避免短时间内重复告警。

### 5. 如何防止服务自身死机？

启用心跳监控（Healthchecks.io），当服务超过60秒未发送心跳时会自动告警。

### 6. 可以发送邮件告警吗？

当前版本只支持钉钉推送。如需邮件，可以使用钉钉的邮件转发功能。

### 7. 日志文件在哪里？

- 应用日志：`logs/monitor.log`
- 服务日志：`logs/service_stdout.log` 和 `logs/service_stderr.log`

### 8. 如何让外网访问Web界面？

**不推荐**将Web界面暴露到公网。如需远程访问，建议使用VPN或内网穿透工具（如frp）。

## 项目结构

```
monitor/
├── main.py              # 主入口，启动多线程
├── monitor.py           # 进程监控核心逻辑
├── notifier.py          # 钉钉推送模块
├── heartbeat.py         # Healthchecks.io心跳模块
├── web.py               # Flask Web界面
├── config.json          # 配置文件
├── requirements.txt     # Python依赖
├── templates/
│   └── index.html       # Web管理界面
├── build.bat            # 打包脚本
├── install_service.bat  # 服务安装脚本
├── uninstall_service.bat # 服务卸载脚本
└── README.md
```

## 技术栈

- **进程检查** - psutil
- **Web框架** - Flask
- **HTTP请求** - requests
- **文件锁** - filelock
- **打包工具** - PyInstaller
- **服务管理** - NSSM

## 设计原则

这个项目遵循 **Linus Torvalds** 的代码哲学：

1. **简单至上** - 代码总计不到500行，没有复杂的架构和过度设计
2. **消除特殊情况** - 使用简单的状态机，没有复杂的条件分支
3. **数据结构优先** - 核心只有三个数据：进程列表、状态字典、时间戳
4. **实用主义** - 解决真实问题，不追求理论完美

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 作者

Generated with Claude Code

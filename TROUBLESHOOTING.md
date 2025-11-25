# 钉钉推送故障排查指南

## 错误: ConnectionResetError(10054)

### 已应用的修复（notifier.py）

1. **增强HTTP会话**
   - 添加Session复用
   - 配置连接池（单连接，避免复用问题）
   - 设置User-Agent
   - 禁用Keep-Alive

2. **改进重试策略**
   - 递增等待时间：3秒 → 6秒 → 9秒
   - 详细的错误分类日志

3. **超时优化**
   - 连接超时：5秒
   - 读取超时：10秒

---

## 如果问题仍然存在

### 方法1: 检查Webhook URL

```bash
# 在命令行测试钉钉Webhook
curl -X POST "你的Webhook URL" \
  -H "Content-Type: application/json" \
  -d '{"msgtype":"text","text":{"content":"测试消息"}}'
```

### 方法2: 检查网络环境

1. **防火墙/杀毒软件**
   - 临时关闭防火墙测试
   - 将Python添加到白名单

2. **企业网络代理**
   如果在企业网络，编辑 `config.json` 添加：

   ```json
   {
     "notification": {
       "dingtalk_webhook": "你的URL",
       "proxy": {
         "http": "http://proxy.company.com:8080",
         "https": "http://proxy.company.com:8080"
       }
     }
   }
   ```

3. **DNS问题**
   ```bash
   # 测试DNS解析
   ping oapi.dingtalk.com
   nslookup oapi.dingtalk.com
   ```

### 方法3: 禁用SSL验证（仅测试用）

如果确定是SSL证书问题，临时禁用验证测试：

编辑 `notifier.py` 第82行：
```python
verify=False  # 改为False（不推荐用于生产环境）
```

并在文件开头添加：
```python
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
```

### 方法4: 使用备用通知方式

如果钉钉始终失败，考虑改用：

1. **企业微信机器人**
2. **Server酱** (https://sct.ftqq.com/)
3. **Bark** (iOS推送)
4. **邮件通知**（虽然延迟较高）

---

## 调试步骤

### 1. 启用详细日志

编辑 `main.py`，将日志级别改为DEBUG：

```python
# 第25行附近
logger.setLevel(logging.DEBUG)  # 改为DEBUG
console_handler.setLevel(logging.DEBUG)
```

### 2. 手动测试钉钉推送

创建测试脚本 `test_dingtalk.py`：

```python
import requests

webhook = "你的钉钉Webhook URL"

payload = {
    "msgtype": "text",
    "text": {"content": "手动测试消息"}
}

try:
    response = requests.post(
        webhook,
        json=payload,
        timeout=10,
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0',
            'Connection': 'close'
        }
    )

    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
```

运行：
```bash
python test_dingtalk.py
```

### 3. 检查Windows系统

```powershell
# 检查网络连接
netstat -ano | findstr "443"

# 测试到钉钉服务器的连接
Test-NetConnection -ComputerName oapi.dingtalk.com -Port 443

# 检查代理设置
netsh winhttp show proxy
```

---

## 常见原因和解决方案

| 原因 | 症状 | 解决方案 |
|------|------|----------|
| 防火墙拦截 | 连接超时 | 添加Python到白名单 |
| 企业代理 | 连接重置 | 配置代理设置 |
| SSL证书问题 | SSLError | 更新证书或临时禁用验证 |
| DNS解析失败 | ConnectionError | 更换DNS服务器 |
| 钉钉API限流 | HTTP 429 | 增加重试间隔 |
| Webhook过期 | errcode != 0 | 重新生成机器人 |

---

## 联系方式

如果问题依然无法解决，请提供：

1. 完整的错误日志
2. 网络环境描述（公司/家庭/VPN）
3. Windows版本和Python版本
4. `test_dingtalk.py` 的运行结果

创建GitHub Issue: https://github.com/miaoxiannv/monitor/issues

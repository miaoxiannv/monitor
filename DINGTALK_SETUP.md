# 钉钉机器人配置指南

## 钉钉机器人安全设置说明

钉钉自定义机器人支持3种安全设置方式，本项目已全部支持：

### 方式1：加签（推荐）⭐

**优点：** 最安全，不需要修改代码逻辑

**配置步骤：**

1. 打开钉钉群 → **群设置** → **智能群助手** → **添加机器人** → **自定义**

2. 填写机器人名称（如"进程监控"）

3. 安全设置选择 **【加签】**

4. 复制生成的 **密钥（secret）**，格式类似：
   ```
   SEC1234567890abcdefghijklmnopqrstuvwxyz1234567890
   ```

5. 复制 **Webhook URL**，格式：
   ```
   https://oapi.dingtalk.com/robot/send?access_token=xxxxxx
   ```

6. 编辑 `config.json`：
   ```json
   {
     "notification": {
       "dingtalk_webhook": "https://oapi.dingtalk.com/robot/send?access_token=你的token",
       "dingtalk_secret": "SEC1234567890abcdefghijklmnopqrstuvwxyz1234567890"
     }
   }
   ```

7. 测试：
   ```bash
   python test_dingtalk.py
   ```

---

### 方式2：自定义关键词

**优点：** 配置简单

**配置步骤：**

1. 安全设置选择 **【自定义关键词】**

2. 添加关键词，例如：`监控`、`告警`、`测试`

3. 复制 **Webhook URL**

4. 编辑 `config.json`（**不需要配置secret**）：
   ```json
   {
     "notification": {
       "dingtalk_webhook": "https://oapi.dingtalk.com/robot/send?access_token=你的token"
     }
   }
   ```

5. **重要：** 确保发送的消息包含你设置的关键词
   - 系统默认消息已包含"告警"、"监控"等关键词
   - 如果自定义了其他关键词，需要修改代码中的消息模板

---

### 方式3：IP地址白名单

**优点：** 限制特定IP访问

**配置步骤：**

1. 安全设置选择 **【IP地址】**

2. 添加你服务器的**公网IP**地址
   - 查看公网IP：访问 https://ip.cn
   - 如果是动态IP，不推荐此方式

3. 复制 **Webhook URL**

4. 编辑 `config.json`（**不需要配置secret**）：
   ```json
   {
     "notification": {
       "dingtalk_webhook": "https://oapi.dingtalk.com/robot/send?access_token=你的token"
     }
   }
   ```

⚠️ **注意：** 如果IP改变，需要重新配置白名单

---

## 常见错误代码

| 错误代码 | 错误信息 | 原因 | 解决方案 |
|---------|---------|------|---------|
| 310000 | 签名不匹配 | secret错误或未配置 | 检查config.json中的secret是否正确 |
| 300001 | 关键词不匹配 | 消息中未包含关键词 | 确保消息包含设置的关键词 |
| 300002 | IP地址不在白名单 | IP不匹配 | 更新白名单或使用加签方式 |

---

## 如何获取密钥（Secret）

### 创建新机器人时获取

1. 添加机器人 → 选择【加签】
2. 钉钉会显示一个以 `SEC` 开头的密钥
3. **立即复制保存！**（关闭后无法再查看）

### 已创建机器人如何查看Secret

⚠️ **钉钉不支持查看已创建机器人的Secret！**

**解决方案：**
1. 删除旧机器人
2. 重新创建一个新机器人
3. 复制新的Webhook和Secret

或者：
1. 改用【自定义关键词】方式
2. 不需要配置secret

---

## 测试配置

运行测试脚本验证配置：

```bash
python test_dingtalk.py
```

**成功输出示例：**
```
============================================================
钉钉Webhook连接测试
============================================================

Webhook URL: https://oapi.dingtalk.com/robot/send?access...
Secret: ******************** (已配置)

✅ 使用加签模式
   时间戳: 1700000000000
   签名: 2Xs3...

正在发送测试消息...

>>> 发送测试消息
状态码: 200
响应: {
  "errcode": 0,
  "errmsg": "ok"
}

============================================================
🎉 测试成功！请检查钉钉群是否收到消息
============================================================
```

---

## 推荐配置

✅ **生产环境：** 使用【加签】方式
✅ **测试环境：** 使用【自定义关键词】方式
❌ **不推荐：** IP白名单（除非固定IP）

---

## 参考链接

- 钉钉机器人官方文档：https://open.dingtalk.com/document/robots/custom-robot-access
- 加签算法说明：https://open.dingtalk.com/document/robots/customize-robot-security-settings

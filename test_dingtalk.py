"""
钉钉推送测试脚本 - 用于排查连接问题
支持加签验证
"""
import requests
import json
import sys
import time
import hmac
import hashlib
import base64
import urllib.parse


def generate_sign(secret):
    """生成钉钉加签"""
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode('utf-8')
    string_to_sign = f'{timestamp}\n{secret}'
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


def test_dingtalk(webhook_url, secret=None):
    """测试钉钉Webhook连接"""

    print("=" * 60)
    print("钉钉Webhook连接测试")
    print("=" * 60)
    print()

    if not webhook_url or webhook_url == "YOUR_ACCESS_TOKEN_HERE":
        print("❌ 错误: 请先配置Webhook URL")
        print("编辑 config.json 填入正确的钉钉机器人Webhook")
        return False

    print(f"Webhook URL: {webhook_url[:50]}...")
    if secret:
        print(f"Secret: {'*' * 20} (已配置)")
    else:
        print("Secret: 未配置（使用关键词或IP白名单验证）")
    print()

    payload = {
        "msgtype": "text",
        "text": {
            "content": "【测试消息】\n这是一条测试推送，如果收到说明配置正确！"
        }
    }

    # 构造最终URL
    if secret:
        timestamp, sign = generate_sign(secret)
        final_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"
        print(f"✅ 使用加签模式")
        print(f"   时间戳: {timestamp}")
        print(f"   签名: {sign[:30]}...")
    else:
        final_url = webhook_url
        print("⚠️  未使用加签（确保配置了关键词或IP白名单）")

    print()
    print("正在发送测试消息...")
    print()

    try:
        # 发送带签名的请求
        print(">>> 发送测试消息")
        response = requests.post(
            final_url,
            json=payload,
            timeout=10,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Connection': 'close'
            }
        )

        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        print()

        if response.status_code == 200 and result.get("errcode") == 0:
            print("=" * 60)
            print("🎉 测试成功！请检查钉钉群是否收到消息")
            print("=" * 60)
            return True
        else:
            error_msg = result.get('errmsg', '未知错误')
            print(f"❌ 发送失败: {error_msg}")

            # 根据错误代码给出建议
            errcode = result.get('errcode')
            if errcode == 310000:
                print()
                print("💡 解决方案:")
                print("1. 检查 config.json 中的 dingtalk_secret 是否正确")
                print("2. 在钉钉机器人设置中，复制完整的 secret（密钥）")
                print("3. Secret 格式类似: SEC1234567890abcdef...")
                print("4. 确认机器人安全设置选择的是【加签】方式")
            elif errcode == 300001:
                print()
                print("💡 解决方案:")
                print("1. 检查消息中是否包含配置的【自定义关键词】")
                print("2. 或者改用【加签】安全设置")

            return False

    except requests.exceptions.SSLError as e:
        print(f"❌ SSL证书验证失败: {e}")
        print()
        print("可能的解决方案:")
        print("1. 检查系统时间是否正确")
        print("2. 更新 certifi 证书: pip install --upgrade certifi")
        print("3. 临时禁用SSL验证（不推荐）")

    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接错误: {e}")
        print()
        print("可能的原因:")
        print("1. 网络连接问题")
        print("2. 防火墙拦截")
        print("3. 需要配置代理")
        print("4. DNS解析失败")

    except requests.exceptions.Timeout as e:
        print(f"❌ 请求超时: {e}")
        print()
        print("可能的原因:")
        print("1. 网络速度慢")
        print("2. 钉钉服务器响应慢")
        print("3. 防火墙延迟")

    except Exception as e:
        print(f"❌ 未知错误: {e}")
        import traceback
        print()
        print("详细错误信息:")
        traceback.print_exc()

    print()
    print("=" * 60)
    print("测试失败，请参考 TROUBLESHOOTING.md 进行排查")
    print("=" * 60)
    return False


if __name__ == "__main__":
    # 从config.json读取Webhook和Secret
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            notification_config = config.get("notification", {})
            webhook = notification_config.get("dingtalk_webhook", "")
            secret = notification_config.get("dingtalk_secret", "")
    except FileNotFoundError:
        print("❌ 错误: 未找到 config.json")
        print("请确保在项目根目录运行此脚本")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        sys.exit(1)

    # 或者从命令行参数读取
    if len(sys.argv) > 1:
        webhook = sys.argv[1]
        secret = sys.argv[2] if len(sys.argv) > 2 else ""
        print(f"使用命令行参数")

    success = test_dingtalk(webhook, secret)
    sys.exit(0 if success else 1)

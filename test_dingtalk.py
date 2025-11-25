"""
钉钉推送测试脚本 - 用于排查连接问题
"""
import requests
import json
import sys

def test_dingtalk(webhook_url):
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
    print()

    payload = {
        "msgtype": "text",
        "text": {
            "content": "【测试消息】\n这是一条测试推送，如果收到说明配置正确！"
        }
    }

    print("正在发送测试消息...")
    print()

    try:
        # 方法1: 使用简单请求
        print(">>> 方法1: 简单POST请求")
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10
        )

        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if response.status_code == 200 and result.get("errcode") == 0:
            print("✅ 方法1成功！")
        else:
            print(f"❌ 方法1失败: {result.get('errmsg', '未知错误')}")

        print()

        # 方法2: 带请求头
        print(">>> 方法2: 带完整请求头")
        response2 = requests.post(
            webhook_url,
            json=payload,
            timeout=10,
            headers={
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Connection': 'close'
            }
        )

        print(f"状态码: {response2.status_code}")
        result2 = response2.json()
        print(f"响应: {json.dumps(result2, ensure_ascii=False, indent=2)}")

        if response2.status_code == 200 and result2.get("errcode") == 0:
            print("✅ 方法2成功！")
            print()
            print("=" * 60)
            print("🎉 测试通过！请检查钉钉群是否收到消息")
            print("=" * 60)
            return True
        else:
            print(f"❌ 方法2失败: {result2.get('errmsg', '未知错误')}")

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
    # 从config.json读取Webhook
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            webhook = config.get("notification", {}).get("dingtalk_webhook", "")
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
        print(f"使用命令行参数的Webhook")

    success = test_dingtalk(webhook)
    sys.exit(0 if success else 1)

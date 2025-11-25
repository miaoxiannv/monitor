#!/usr/bin/env python3
"""
进程监控Agent - 运行在被监控的Linux机器上
提供HTTP API返回当前运行的进程列表
"""
import os
import sys
from flask import Flask, jsonify
import psutil
import socket

app = Flask(__name__)

# 配置
AGENT_VERSION = "1.0.0"
AGENT_PORT = int(os.getenv('AGENT_PORT', 8888))
AGENT_HOST = os.getenv('AGENT_HOST', '0.0.0.0')


@app.route('/api/health')
def health():
    """健康检查端点"""
    return jsonify({
        "status": "ok",
        "version": AGENT_VERSION,
        "hostname": socket.gethostname()
    })


@app.route('/api/processes')
def get_processes():
    """
    返回当前运行的所有进程列表

    返回格式：
    {
        "status": "ok",
        "hostname": "server1",
        "processes": ["nginx", "python3", "mysql"],
        "count": 3
    }
    """
    try:
        # 获取所有进程名（去重）
        process_names = set()
        for proc in psutil.process_iter(['name']):
            try:
                process_names.add(proc.info['name'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return jsonify({
            "status": "ok",
            "hostname": socket.gethostname(),
            "processes": sorted(list(process_names)),
            "count": len(process_names)
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/process/<process_name>')
def check_process(process_name):
    """
    检查特定进程是否运行

    返回格式：
    {
        "status": "ok",
        "process": "nginx",
        "running": true,
        "count": 2
    }
    """
    try:
        count = 0
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] == process_name:
                    count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return jsonify({
            "status": "ok",
            "process": process_name,
            "running": count > 0,
            "count": count
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    print("=" * 60)
    print(f"进程监控Agent v{AGENT_VERSION}")
    print("=" * 60)
    print(f"主机名: {socket.gethostname()}")
    print(f"监听地址: {AGENT_HOST}:{AGENT_PORT}")
    print()
    print("API端点:")
    print(f"  - GET /api/health          - 健康检查")
    print(f"  - GET /api/processes       - 获取所有进程")
    print(f"  - GET /api/process/<name>  - 检查特定进程")
    print()
    print("按 Ctrl+C 停止服务")
    print("=" * 60)

    try:
        app.run(
            host=AGENT_HOST,
            port=AGENT_PORT,
            debug=False
        )
    except KeyboardInterrupt:
        print("\n服务已停止")
        sys.exit(0)

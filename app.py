#!/usr/bin/env python3
"""
Agnes AI Studio - 图片 & 视频生成可视化工具
后端服务 (Flask) - 支持 PyInstaller 打包为独立 .exe
"""

import os
import sys
import threading
import webbrowser

# 禁用 Windows 控制台快速编辑模式（防止点击控制台窗口导致程序卡住）
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        # 清除 ENABLE_QUICK_EDIT_MODE (0x0040)，保留 ENABLE_EXTENDED_FLAGS (0x0080)
        kernel32.SetConsoleMode(handle, (mode.value & ~0x0040) | 0x0080)
    except Exception:
        pass  # 非控制台环境（如服务）忽略

from src import create_app
from src.config import get_config_path, shutdown_event

app = create_app()


def main():
    """主入口"""
    print("=" * 60)
    print("  Agnes AI Studio - 图片 & 视频生成可视化工具 v1.0")
    print("  项目目录: " + os.path.dirname(get_config_path()))
    print("=" * 60)
    print("  本地访问: http://127.0.0.1:5000")
    print("  局域网访问: http://你的IP地址:5000")
    print("  按 Ctrl+C 停止服务")
    print("=" * 60)

    # 自动打开浏览器
    threading.Timer(1.5, lambda: webbrowser.open('http://127.0.0.1:5000')).start()

    print("  提示: 按 Ctrl+C 可停止服务")
    print("=" * 60)

    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n[关闭] 收到 Ctrl+C，正在停止服务...")
        shutdown_event.set()
        print("[关闭] 服务已停止")


if __name__ == '__main__':
    main()

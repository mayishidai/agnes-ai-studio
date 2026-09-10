#!/bin/bash
# Agnes AI Studio 一键启动：本地服务 + Cloudflare 公网隧道
#
# 用途：沙箱休眠或重启后，应用/隧道进程会退出、旧公网地址失效。
#       运行本脚本可一次性拉起本地服务并重新获取可用的公网访问地址。
#
# 用法：./start_with_tunnel.sh
#
# 注意：Cloudflare 临时隧道（trycloudflare.com）的地址每次都会变化，
#       需要固定域名请改用 named tunnel 并配置自己的域名。

cd "$(dirname "$0")" || exit 1

echo "=== Agnes AI Studio 启动中 ==="

# ---- 1. 启动本地应用 ----
# 沙箱休眠恢复初期网络栈可能未就绪，curl 探测连续失败才判定未运行，避免误启动第二实例
APP_RUNNING=0
for i in 1 2 3; do
    if curl -s -o /dev/null --max-time 3 http://127.0.0.1:5000/; then
        APP_RUNNING=1
        break
    fi
    sleep 2
done

if [ "$APP_RUNNING" = "1" ]; then
    echo "[1/3] 应用已在运行，跳过启动"
else
    echo "[1/3] 启动本地应用 (端口 5000)..."
    # 追加写日志（>>），避免截断仍在运行实例的日志文件
    setsid python3 app.py >> /tmp/app.log 2>&1 < /dev/null &
    sleep 6
fi
LOCAL_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://127.0.0.1:5000/)
echo "      本地状态: HTTP ${LOCAL_CODE}"
if [ "$LOCAL_CODE" != "200" ]; then
    echo "本地启动失败，请查看 /tmp/app.log"
    exit 1
fi

# ---- 2. 启动 Cloudflare 隧道（http2 协议，绕开被网络阻断的 QUIC/UDP 7844）----
echo "[2/3] 启动 Cloudflare 公网隧道..."
rm -f /tmp/cf.log
setsid cloudflared tunnel --url http://localhost:5000 --protocol http2 > /tmp/cf.log 2>&1 < /dev/null &

# ---- 3. 等待隧道就绪并验证连通 ----
echo "[3/3] 等待隧道就绪..."
for i in $(seq 1 20); do
    URL=$(grep -oE "https://[a-z0-9.-]+\.trycloudflare\.com" /tmp/cf.log 2>/dev/null | head -1)
    if [ -n "$URL" ]; then
        CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 20 "$URL")
        if [ "$CODE" = "200" ]; then
            echo ""
            echo "  公网访问地址: ${URL}"
            echo "  本地访问地址: http://127.0.0.1:5000"
            echo ""
            echo "  提示: 这是临时地址，沙箱休眠或重启后会失效，重跑本脚本即可获取新地址。"
            exit 0
        fi
    fi
    sleep 3
done

echo "隧道启动超时或不可达，请查看 /tmp/cf.log"
exit 1

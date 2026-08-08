#!/bin/bash
# Agnes AI Studio 一键启动脚本 (Flask + Cloudflare 命名隧道)
# 用途：沙箱休眠/进程掉线后，一键恢复公网访问
# 用法：bash /workspace/agnes-ai-studio/start_all.sh

set -e
cd /workspace/agnes-ai-studio

echo "[1/2] 检查并启动 Flask (本地 127.0.0.1:5000) ..."
if curl -s -o /dev/null --max-time 3 http://127.0.0.1:5000/; then
  echo "  Flask 已在运行，跳过"
else
  nohup python3 app.py > server.log 2>&1 &
  sleep 4
  curl -s -o /dev/null -w "  Flask 启动完成 -> HTTP %{http_code}\n" --max-time 5 http://127.0.0.1:5000/ \
    || echo "  ⚠ Flask 启动失败，请查看 server.log"
fi

echo "[2/2] 检查并启动 Cloudflare 命名隧道 ..."
if pgrep -x cloudflared >/dev/null; then
  echo "  隧道已在运行，跳过"
else
  if [ -f /root/.cloudflared/tunnel_token.txt ]; then
    TOKEN=$(cat /root/.cloudflared/tunnel_token.txt)
    nohup cloudflared tunnel run --token "$TOKEN" --url http://127.0.0.1:5000 --protocol http2 > named-tunnel.log 2>&1 &
    sleep 7
  else
    echo "  ❌ 隧道 token 文件丢失(/root/.cloudflared/tunnel_token.txt)，需重新获取"
    exit 1
  fi
fi

echo ""
echo "✅ 完成。访问地址: https://agnes.abcc.us.ci"
echo "   如仍 530，稍候数秒让隧道重新注册后再试。"

#!/bin/bash
echo "============================================="
echo "  Agnes AI Studio - macOS 打包工具"
echo "============================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3，请先安装 Python 3.8+"
    echo "  安装方式: brew install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[信息] Python 版本: $PYTHON_VERSION"

# 检查最低版本
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[错误] Python 版本需要 3.8+，当前为 $PYTHON_VERSION"
    exit 1
fi

echo ""
echo "[1/3] 安装 PyInstaller 和项目依赖..."
pip3 install pyinstaller flask flask-cors requests imageio-ffmpeg -q

echo ""
echo "[2/3] 检查 ffmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "  ✓ 系统已安装 ffmpeg"
else
    echo "  ✓ 将使用 imageio-ffmpeg 内置的 ffmpeg"
fi

echo ""
echo "[3/3] 开始打包 macOS 版本..."
echo ""
echo "  这可能需要几分钟，请耐心等待..."
echo ""

pyinstaller --clean --noconfirm Agnes-AI-Studio-mac.spec

if [ $? -ne 0 ]; then
    echo ""
    echo "[失败] 打包出错，请检查上方错误信息"
    exit 1
fi

echo ""
echo "============================================="
echo "  打包完成！"
echo ""
echo "  输出文件: dist/Agnes-AI-Studio.app"
echo ""
echo "  使用方法:"
echo "    1. 双击 dist/Agnes-AI-Studio.app 运行"
echo "    2. 或在终端执行: open dist/Agnes-AI-Studio.app"
echo "    3. 浏览器会自动打开 http://127.0.0.1:5000"
echo ""
echo "  如需命令行运行:"
echo "    ./dist/Agnes-AI-Studio.app/Contents/MacOS/Agnes-AI-Studio"
echo "============================================="
echo ""

# 尝试打开 Finder 显示输出目录
if command -v open &> /dev/null; then
    open dist/
fi

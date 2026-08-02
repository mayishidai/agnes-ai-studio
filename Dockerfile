FROM python:3.11-slim

# 安装系统依赖（ffmpeg 等）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建数据目录
RUN mkdir -p /app/data/videos /app/data/pictures /app/data/dramas

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["python", "app.py"]

# 智能客服系统 Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements_new.txt* ./
COPY requirements.txt* ./

# 安装Python依赖
RUN if [ -f requirements_new.txt ]; then pip install --no-cache-dir -r requirements_new.txt; \
    elif [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; \
    else echo "No requirements file found"; fi

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p data logs static

# 暴露端口（使用8001端口，匹配api_server_simple.py）
EXPOSE 8001

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# 启动命令（使用简化版API服务器）
CMD ["python", "api_server_simple.py"]
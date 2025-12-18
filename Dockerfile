# 使用Python 3.11官方镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 更换为国内Debian源并安装系统依赖
# 注意：如果你在requirements.txt中改用pymysql，可以移除gcc和default-libmysqlclient-dev
RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && \
    apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 使用国内pip源安装Python依赖
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 暴露端口 (EXPOSE在Docker网络中主要用于文档说明，实际端口由Render分配)
EXPOSE $PORT

# 健康检查 (使用Render提供的$PORT变量，并确保后端有这个端点)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# 启动命令 (关键修改：使用$PORT，并移除--reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "$PORT"]

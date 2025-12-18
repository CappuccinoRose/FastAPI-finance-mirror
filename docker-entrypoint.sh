#!/bin/bash
set -e

echo "等待数据库就绪..."

# 使用 Python 脚本等待数据库就绪
python3 wait-for-db.py

if [ $? -ne 0 ]; then
    echo "错误: 无法连接到数据库"
    exit 1
fi

echo "数据库已就绪，开始运行数据库迁移..."

# 运行数据库迁移
alembic upgrade head || {
    echo "警告: 数据库迁移失败，但继续启动应用..."
    # 继续执行，不退出
}

echo "启动应用..."

# Railway 会自动提供 PORT 环境变量，如果没有则使用 8000
PORT=${PORT:-8000}
echo "使用端口: $PORT"

# 如果传入了命令，使用传入的命令；否则使用默认命令
if [ "$#" -gt 0 ]; then
    # 如果传入的命令包含 uvicorn，替换端口
    if echo "$*" | grep -q uvicorn; then
        exec "$@"
    else
        exec "$@" --port "$PORT"
    fi
else
    # 使用环境变量 PORT
    exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
fi

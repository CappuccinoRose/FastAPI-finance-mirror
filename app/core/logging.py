# app/core/logging.py
# 检验运行问题的日志配置文件
import logging
import sys

def setup_logging():
    # 配置日志格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 只配置控制台处理器，将日志输出到标准输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # 设置 uvicorn 的日志级别
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

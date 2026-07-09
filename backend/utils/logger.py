"""统一日志配置模块

日志输出到两个地方：
1. 控制台（彩色，方便开发时看）
2. 本地文件 logs/app.log（按天轮转，保留 30 天）

使用方式：
    from utils.logger import logger
    logger.info("xxx")
    logger.error("xxx", exc_info=True)
"""

import logging
import os
from logging.handlers import TimedRotatingFileHandler

# 日志目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# 自定义格式
class ColorFormatter(logging.Formatter):
    """控制台彩色输出"""
    COLORS = {
        logging.DEBUG: "\033[36m",     # cyan
        logging.INFO: "\033[32m",      # green
        logging.WARNING: "\033[33m",   # yellow
        logging.ERROR: "\033[31m",     # red
        logging.CRITICAL: "\033[35m",  # magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        # 复制 record 避免修改原始 levelname 影响其他 handler
        import copy
        record = copy.copy(record)
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{record.levelname:<8}{self.RESET}"
        return super().format(record)


def setup_logger(name: str = "fingerprint") -> logging.Logger:
    """创建并配置 logger 实例"""
    log = logging.getLogger(name)

    # 避免重复添加 handler（uvicorn --reload 可能多次初始化）
    if log.handlers:
        return log

    log.setLevel(logging.DEBUG)

    fmt = "%(asctime)s │ %(levelname)s │ %(name)s │ %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    # 控制台 handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColorFormatter(fmt, datefmt=datefmt))

    # 文件 handler（按天轮转，保留 30 天）
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(LOG_DIR, "app.log"),
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(fmt, datefmt=datefmt))

    log.addHandler(console_handler)
    log.addHandler(file_handler)

    return log


# 全局 logger 实例，直接 import 使用
logger = setup_logger()

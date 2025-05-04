import logging

def setup_logger(LogLevel: int = logging.INFO):
    # 設定通用的日誌格式和處理器
    logger = logging.getLogger()  # 根 logger
    logger.setLevel(logging.DEBUG)

    log_format = '%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(lineno)d - %(message)s'
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(logging.Formatter(log_format))

    # File handler
    file_handler = logging.FileHandler("run.log", mode="w", encoding="utf-8")
    file_handler.setLevel(LogLevel)
    file_handler.setFormatter(logging.Formatter(log_format))

    # 添加處理器到根 logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
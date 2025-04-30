import logging

def setup_logger():
    # 設定通用的日誌格式和處理器
    logger = logging.getLogger()  # 根 logger
    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(logging.Formatter('%(levelname)s - %(name)s - %(funcName)s - %(message)s'))

    # File handler
    file_handler = logging.FileHandler("run.log", mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s'))

    # 添加處理器到根 logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
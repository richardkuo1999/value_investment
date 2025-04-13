import logging

def setup_logger():
    logger = logging.getLogger("shared_logger")
    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter('%(levelname)s - %(funcName)s - %(message)s'))

    # File handler
    file_handler = logging.FileHandler("run.log", mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'))

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger
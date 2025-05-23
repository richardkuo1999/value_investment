import csv
import yaml
import logging
import requests
import aiohttp
from pathlib import Path
from bs4 import BeautifulSoup

from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# from google.oauth2 import service_account
# from googleapiclient.discovery import build
# from googleapiclient.http import MediaFileUpload
# from googleapiclient.errors import HttpError


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}


def logger_create(file_name):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s:%(funcName)s:%(lineno)d - %(message)s",
    )
    logger = logging.getLogger(__name__)
    file_handler = logging.FileHandler("syslog.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s",)
    )
    logger.addHandler(file_handler)
    return logger

logger = logger_create(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(3),
    retry=retry_if_exception_type((aiohttp.ClientError, Exception)),
)
async def fetch_webpage(session, url: str, headers: dict = DEFAULT_HEADERS, timeout: int = 10) -> BeautifulSoup | None:
    try:
        async with session.get(
            url,
            headers=headers,
            timeout=timeout,
            max_line_size=1024**2,
            max_field_size=1024**2,
        ) as response:
            response.raise_for_status()  # 檢查 HTTP 狀態碼
            text = await response.text(encoding="utf-8")  # 強制設置 utf-8 編碼
            return BeautifulSoup(text, "html5lib")
    except aiohttp.ClientError as e:
        logger.error(f"無法獲取網頁 {url}：{e}")
        raise  # 讓 tenacity 處理重試
    except Exception as e:
        logger.error(f"獲取網頁 {url} 時發生意外錯誤：{e}")
        raise


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(3),
    retry=retry_if_exception_type(aiohttp.ClientError),
)
async def fetch_web2json(session, url: str, headers=DEFAULT_HEADERS, timeout=20) -> dict:
    try:
        async with session.get(url, headers=headers, timeout=timeout) as response:
            response.raise_for_status()
            return await response.json(content_type=None)
    except aiohttp.ClientError as e:
        logger.error(f"Failed to fetch JSON from {url}: {e}")
        raise
    except ValueError as e:
        logger.error(f"Failed to parse JSON from {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        return None


def load_token(path="token.yaml"):
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}

def dict2list(data):
    result = []
    for key, value in data.items():
        if isinstance(value, dict):
            result.extend(dict2list(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    result.extend(dict2list(item))
                else:
                    result.append(item)
        else:
            result.append(value)
    return result


def is_ordinary_stock(stock_id):
    return stock_id[0] in "12345678"

def get_profit(target_Price, price):
    return float(target_Price / price - 1) * 100

def get_target(rate, data):
    return rate * data


def get_last_data(result_dir: Path) -> dict:
    datas = {}
    files_processed = 0
    for filepath in result_dir.rglob("*.csv"):
        try:
            with filepath.open(mode="r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    stock_id = row.get("代號")
                    if stock_id and stock_id not in datas:  # Keep the most recent entry
                        converted_row = {}
                        for key, value in row.items():
                            try:
                                converted_row[key] = float(value)
                            except (ValueError, TypeError):
                                converted_row[key] = value
                        datas[stock_id] = converted_row
            files_processed += 1
            logger.debug(f"Processed CSV file: {filepath}")
        except (IOError, csv.Error) as e:
            logger.warning(f"Failed to read CSV file {filepath}: {e}")
            continue

    logger.info(f"Aggregated data for {len(datas)} stocks from {files_processed} files")
    return datas
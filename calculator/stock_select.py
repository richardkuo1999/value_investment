import re
from natsort import natsorted
import os
import sys
import logging

sys.path.append(os.path.dirname(__file__) + "/..")
from utils.utils import fetch_webpage, is_ordinary_stock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_etf_constituents(etf_id: str) -> list[str]:
    url = f"https://www.moneydj.com/ETF/X/Basic/Basic0007B.xdjhtm?etfid={etf_id}.TW"
    try:
        soup = fetch_webpage(url)
        return natsorted({
            match.group(1)
            for a in soup.select("td.col05 a")
            if (href := a.get("href")) and (match := re.search(r"etfid=(\d+)\.", href))
        })
    except Exception as e:
        logger.error(f"[Error] Failed to fetch ETF constituents for {etf_id}: {e}")
        return []

def fetch_investor_stocks(investor_type: str) -> list[str]:
    url = f"https://histock.tw/stock/three.aspx?s={investor_type}"
    try:
        soup = fetch_webpage(url)
        stocks = [
            element.text.strip()
            for element in soup.find_all("span", class_="w58")[::6]
            if is_ordinary_stock(element.text.strip())
        ]
        return stocks
    except Exception as e:
        logger.error(f"Failed to fetch stocks for investor type {investor_type}: {e}")
        return []

def fetch_institutional_top50() -> list[str]:
    investor_types = {"foreign":"a", "investment_trust":"b", "dealers":"c"}
    all_stocks = set()

    for investor_type in investor_types.values():
        stocks = fetch_investor_stocks(investor_type)
        all_stocks.update(stocks)

    return natsorted(all_stocks)

if __name__ == "__main__":
    etf_id = "0050"
    logger.info(f"ETF {etf_id} constituents: {fetch_etf_constituents(etf_id)}")
    
    investor_types = ["foreign", "investment_trust", "dealers"]
    for investor_type in investor_types:
        stocks = fetch_investor_stocks(investor_type)
        logger.info(f"{investor_type.capitalize()} stocks: {stocks}")

    logger.info(f"Top 50 institutional stocks: {fetch_institutional_top50()}")
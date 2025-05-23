import re
import os
import sys
import aiohttp
import asyncio
from natsort import natsorted

sys.path.append(os.path.dirname(__file__) + "/..")

from utils.utils import logger, fetch_webpage, is_ordinary_stock


ETF_BASE_URL = "https://www.moneydj.com/ETF/X/Basic/Basic0007B.xdjhtm?etfid={}.TW"
INVESTOR_URL = "https://histock.tw/stock/three.aspx?s={}"
INVESTOR_TYPES = {"foreign": "a", "investment_trust": "b", "dealers": "c"}

async def fetch_etf_constituents(session, etf_id: str) -> list[str]:
    try:
        soup = await fetch_webpage(session, ETF_BASE_URL.format(etf_id))
        constituents = {
            match.group(1)
            for a in soup.select("td.col05 a")
            if (href := a.get("href")) and (match := re.search(r"etfid=(\d+)\.", href))
        }
        return natsorted(constituents)
    except (ValueError, AttributeError, asyncio.TimeoutError) as e:
        logger.error(f"[Error] Failed to fetch ETF constituents for {etf_id}: {str(e)}")
        return []


async def fetch_investor_stocks(session, investor_type: str) -> list[str]:
    try:
        soup = await fetch_webpage(session, INVESTOR_URL.format(investor_type))
        stocks = [
            element.text.strip()
            for element in soup.find_all("span", class_="w58")[::6]
            if is_ordinary_stock(element.text.strip())
        ]
        return stocks
    except (ValueError, AttributeError, asyncio.TimeoutError) as e:
        logger.error(
            f"Failed to fetch stocks for investor type {investor_type}: {str(e)}"
        )
        return []


async def fetch_institutional_top50(session) -> list[str]:
    tasks = [
        fetch_investor_stocks(session ,investor_type)
        for investor_type in INVESTOR_TYPES.values()
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_stocks = set()

    for result in results:
        if isinstance(result, list):
            all_stocks.update(result)

    return natsorted(all_stocks)


async def main():
    # Fetch ETF constituents
    etf_id = "0050"

    # Fetch stocks for each investor type concurrently
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_etf_constituents(session, etf_id),
            fetch_investor_stocks(session, INVESTOR_TYPES["foreign"]),
            fetch_institutional_top50(session),
        ]
        etf_stocks, investor_stocks, top_50 = await asyncio.gather(*tasks, return_exceptions=True)
    logger.info(f"ETF {etf_id} constituents: {etf_stocks}")

    logger.info(f"foreign stocks (count: {len(investor_stocks)}): {investor_stocks}")

    logger.info(f"Top 50 institutional stocks (count: {len(top_50)}): {top_50}")


if __name__ == "__main__":
    asyncio.run(main())

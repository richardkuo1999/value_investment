import os
import sys
import aiohttp
import asyncio
import logging
import yfinance as yf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YahooFinance:
    SUPPORTED_MARKETS = ["TW", "TWO"]
    async def fetch_data(self, stock_id, market) -> dict:
        try:
            if market not in self.SUPPORTED_MARKETS:
                raise ValueError(f"Market '{market}' is not supported. Use 'TW' or 'TWO'.")
            
            stock = yf.Ticker(f"{stock_id}.{market}")
            hist_price = stock.history(period="5y")

            return {"info": stock.info, "price": hist_price}
        except Exception as e:
            logger.error("Failed to fetch Yahoo Finance data for {}.{}: {}"
                         .format(stock_id, market, e))
            return {}

async def main():
    stock_id = "2330"
    market = "TW"
    yahoo_finance = YahooFinance()

    tasks = [
        yahoo_finance.fetch_data(stock_id, "TW"),
        yahoo_finance.fetch_data(stock_id, "TWO"),
    ]
    tw_data, two_data = await asyncio.gather(*tasks, return_exceptions=True)
    yahoofinance_data = tw_data or two_data
    # print(yahoofinance_data["info"])
    target_est = yahoofinance_data["info"].get("targetMeanPrice", "")
    peg = yahoofinance_data["info"].get("trailingPegRatio", None)
    business = yahoofinance_data["info"].get("longBusinessSummary", None)
    print(f"1y Target Est for {stock_id}.{market}: {target_est}")
    print(f"trailingPegRatio for {stock_id}.{market}: {peg}")
    print(f"business for {stock_id}.{market}: {business}")

if __name__ == "__main__":
    asyncio.run(main())
import os
import sys
import asyncio
import aiohttp
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

sys.path.append(os.path.dirname(__file__) + "/..")
from utils.utils import logger, load_token

FETCH_URL = "https://api.finmindtrade.com/api/v4/data"
USELIMIT_URL = "https://api.web.finmindtrade.com/v2/user_info"
INFO_HEAD = ["stock_name", "type", "industry_category"]

class Finminder:
    def __init__(self, tokens):
        self.tokens = tokens["FinmindToken"]
        self.current_token_idx = 0
        self.api_request_limit = 600

    async def _rotate_token(self, session):
        self.current_token_idx = (self.current_token_idx + 1) % len(self.tokens)
        user_count = 0

        async def _fetch_token_limit(session, token):
            params = {"token": token}
            try:
                async with session.get(USELIMIT_URL, params=params) as resp:
                    if resp.status == 200:
                        response = await resp.json()
                        return response["api_request_limit"], response["user_count"]
                    else:
                        logger.error(f"Request failed for token with status {resp.status}")
                        return 600, 600
            except Exception as e:
                print(f"Error fetching token {token}: {e}")
                return 600, 600
    
        tasks = [
            _fetch_token_limit(session, token)
            for token in self.tokens
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for idx, (api_limit, count) in enumerate(results):
            self.api_request_limit = api_limit
            user_count += count
        if user_count + 30 >= self.api_request_limit:
            logger.warning(f"Token reached usage limit. Sleep 300s")
            await asyncio.sleep(300)
            await self._rotate_token(session)
        

    async def fetch_data(self, session, stock_id, start_date):
        per, pbr = await self.get_per_pbr(session, stock_id, start_date)
        return {
            "per_pbr": {"per": per, "pbr": pbr},
        }
    
    async def _fetch_data(self, session, dataset: str, params = None) -> pd.DataFrame:
        params = params or {}
        params.update({
            "dataset": dataset,
            "token": self.tokens[self.current_token_idx]
        })

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_fixed(10),
            retry=retry_if_exception_type((aiohttp.ClientError, OverflowError)),
        )
        async def _request():
            await self._rotate_token(session)
            async with session.get(FETCH_URL, params=params) as resp:
                if resp.status == 402:
                    params["token"] = self.tokens[self.current_token_idx]
                    logger.warning(f"Token {self.current_token_idx} reached usage limit")
                    raise OverflowError(f"Token {self.current_token_idx} reached usage limit")
                resp.raise_for_status()
                return await resp.json()
        try:
            data = await _request()
            logger.debug(f"Retrieved {dataset} for {params.get('data_id', 'all')}")
            return pd.DataFrame(data["data"])
        except Exception as e:
            logger.error(f"Failed to retrieve {dataset}: {e}")
            raise

    async def get_taiwan_option_daily(self, session, option_id: str, start_date: str) -> pd.DataFrame:
            return await self._fetch_data(session, "TaiwanOptionDaily", 
                                          {"data_id": option_id, "start_date": start_date}
                                          )

    async def fetch_stock_info(self, session, stock_id: str, tag1: str, tag2: str = INFO_HEAD):
        """fetch the stock info according to tag2

        Args:
            stock_id (str): stock number
            tag1 (str): stock_id is stock number or stock name
            tag2 (str): stock_name or Listed Company/OTC

        Returns:
            str: according to yout tag2 what you want to get
        """
        try:
            stock_info = await self._fetch_data(session, "TaiwanStockInfo")
            result = stock_info[stock_info[tag1] == stock_id]
            if result.empty:
                logger.warning(f"No stock info found for {tag1}={stock_id}")
                return None
            return result.iloc[0][tag2]
        except Exception as e:
            logger.error(f"Failed to retrieve stock info for {tag1}={stock_id}, tag2={tag2}: {e}")
            return None

    async def get_eps(self, session, stock_id, start_date):
        if not stock_id or not start_date:
            raise ValueError("stock_id and start_date must be set")
        try:
            df = await self._fetch_data(
                session, "TaiwanStockFinancialStatements", 
                {"data_id": stock_id, "start_date": start_date}
            )
            if df.empty or "type" not in df or "value" not in df:
                logger.warning(f"No EPS data found for stock {stock_id}")
                return []
            return df[df["type"] == "EPS"]["value"].astype(float).tolist()
        except Exception as e:
            logger.error(f"Failed to retrieve EPS for stock {stock_id}: {e}")
            return []

    async def get_closing_price(self, session, stock_id, start_date):
        if not stock_id or not start_date:
            raise ValueError("stock_id and start_date must be set")
        try:
            df = await self._fetch_data(
                session, "TaiwanStockPrice", 
                {"data_id": stock_id, "start_date": start_date}
            )
            if df.empty or "date" not in df or "close" not in df:
                logger.warning(f"No closing price data found for stock {stock_id}")
                return None
            return df
        except Exception as e:
            logger.error(f"Failed to retrieve closing prices for stock {stock_id}: {e}")
            return None

    async def get_per_pbr(self, session, stock_id, start_date):
        if not stock_id or not start_date:
            raise ValueError("stock_id and start_date must be set")
        try:
            df = await self._fetch_data(
                session, "TaiwanStockPER", 
                {"data_id": stock_id, "start_date": start_date}
            )
            if df.empty or "PER" not in df or "PBR" not in df:
                logger.warning(f"No PER/PBR data found for stock {stock_id}")
                return [], []
            return df["PER"].astype(float).tolist(), df["PBR"].astype(float).tolist()
        except Exception as e:
            logger.error(f"Failed to retrieve PER/PBR for stock {stock_id}: {e}")
            return [], []


async def main():
    token = load_token()
    finminder = Finminder(token)
    stock_id = "2330"
    start_date = "2024-12-01"
    futures_id = "TXO"

    async with aiohttp.ClientSession() as session:
        tasks = [
            finminder.fetch_stock_info(session, stock_id, "stock_id"),
            finminder.fetch_data(session, stock_id, start_date),
            finminder.get_taiwan_option_daily(session, futures_id, start_date) 
        ]
        stock_info, data, option_data = await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"PER/PBR: {data['per_pbr']}")
        logger.info(f"stock_name: {stock_info['stock_name']}")
        logger.info(f"TXO option: {option_data}")


if __name__ == "__main__":
    asyncio.run(main())
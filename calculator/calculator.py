import os
import sys
import asyncio
import aiohttp
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(__file__) + "/..")

from Database.Finmind import Finminder
# from Database.Goodinfo import Goodinfo
from Database.YahooFinance import YahooFinance
from Database.Anue import ANUE
from utils.Math import Math

from utils.utils import logger


QUARTILE_TITLES = ["25%", "50%", "75%", "平均"]
MEAN_REVERSION_TITLES = {
    "prob": ["往上機率", "區間震盪機率", "往下機率"],
    "TL": ["TL價"],
    "expect": ["保守做多期望值", "樂觀做多期望值", "樂觀做空期望值"],
    "targetprice": ["超極樂觀", "極樂觀", "樂觀", "趨勢", "悲觀", "極悲觀", "超極悲觀"],
}

class Stock_Predictor:
    def __init__(self, parameter, token, catch_url):
        self.level, self.year = parameter
        self.catch_url = catch_url
        self.start_date = (datetime.now() - timedelta(days=self.year * 365)).strftime(
            "%Y-%m-%d"
        )

        self.finmind = Finminder(token)
        # self.goodinfo = Goodinfo()
        self.anue = ANUE(self.catch_url, self.level)
        self.yahoofinance = YahooFinance()


    async def fetch_data(self, session, stock_id):
        start_date = self.start_date

        stock_info = \
            await self.finmind.fetch_stock_info(session, stock_id, "stock_id")
        
        self.stock_name = stock_info["stock_name"]
        self.industry_category = stock_info["industry_category"]
        self.market = "TW" if stock_info["type"] == "twse" else "TWO"

        tasks = [
            self.finmind.fetch_data(session, stock_id, start_date),
            self.anue.fetch_data(session, stock_id, self.stock_name),
            self.yahoofinance.fetch_data(stock_id, self.market)
        ]
        finmind_data, anue_data, yahoofinance_data = \
                await asyncio.gather(*tasks, return_exceptions=True)
        
        self.stock_id = stock_id
        
        self.per_datas = finmind_data["per_pbr"]["per"]
        self.pbr_datas = finmind_data["per_pbr"]["pbr"]

        self.factset_data = anue_data

        self.avg1y_target_est = yahoofinance_data["info"].get("targetMeanPrice")
        self.peg = yahoofinance_data["info"].get("trailingPegRatio")
        self.business = yahoofinance_data["info"].get("longBusinessSummary")
        self.gross_margins = yahoofinance_data["info"].get("grossMargins")
        self.market_price = yahoofinance_data["info"].get("regularMarketPrice")
        self.price_datas =  yahoofinance_data["price"]["Close"].values
        self.trailingEps = yahoofinance_data["info"].get("trailingEps")
        self.yahooforwardEps = yahoofinance_data["info"].get("forwardEps")


    async def process(self):
        market_price = self.market_price
        pbr_data = self.pbr_datas
        per_data = self.per_datas

        stock_data = {
            "名稱": self.stock_name,
            "代號": self.stock_id,
            "產業": self.industry_category,
            "資訊": self.business,
            "交易所": self.market,
            "價格": market_price,
            "毛利率": self.gross_margins,
            "EPS(TTM)": self.trailingEps,
            "BPS": market_price / pbr_data[-1] if pbr_data else None,
            "PE(TTM)": per_data[-1] if per_data else None,
            "PB(TTM)": pbr_data[-1] if pbr_data else None,
            "yahooforwardEps": self.yahooforwardEps,
            "Yahoo_1yTargetEst": self.avg1y_target_est,
        }

        # 從 鉅亨網 取得預估eps及市場預估價
        factset_est_price, est_eps, anue_data_time, url = self.factset_data
        stock_data.update(
            {
                "EPS(EST)": est_eps if est_eps else None,
                "PE(EST)": (market_price / est_eps) if est_eps else None,
                "Factest目標價": factset_est_price if factset_est_price else None,
                "資料時間": str(anue_data_time).split(" ")[0].replace("-", "/"),
                "ANUEurl": url,
            }
        )

        # 使用均值回歸預測價格
        df = Math.mean_reversion(self.price_datas)
        for key, value in df.items():
            stock_data.update({t: v for t, v in zip(MEAN_REVERSION_TITLES[key], value)})

        # 使用本益比四分位數預測股價
        df = Math.quartile(self.per_datas)
        stock_data.update({f"PE({t})": d for t, d in zip(QUARTILE_TITLES, df)})

        # 利用本益比標準差預測股價
        df, comp_list = Math.std(self.per_datas)
        stock_data.update({f"PE({t})": df[t][-1] for t in comp_list})

        # 使用股價淨值比四分位數預測股價
        df = Math.quartile(self.pbr_datas)
        stock_data.update({f"PB({t})": d for t, d in zip(QUARTILE_TITLES, df)})

        # 利用股價淨值比標準差預測股價
        df, comp_list = Math.std(self.pbr_datas)
        stock_data.update({f"PB({t})": df[t][-1] for t in comp_list})

        # 取得 PEG
        stock_data["PEG"] = self.peg

        return stock_data


async def calculator(session, stock_list, parameter, tokens, catch_url={}):
    stock_datas = {}
    predictor = Stock_Predictor(parameter, tokens, catch_url)
    for i, stock_id in enumerate(stock_list, start=1):
        logger.info(f"Processing {i}/{len(stock_list)}: {stock_id}")
        try:
            await predictor.fetch_data(session, stock_id)
            stock_datas[stock_id] = await predictor.process()
        except Exception as e:
            logger.error(f"Error processing {stock_id}: {e}")
    return stock_datas


async def main():
    from utils.utils import load_token

    tokens = load_token()
    stock_list = ["2330"]  # Example stock list
    parameter = (1, 5)  # Example parameters
    catch_url = {}  # Example catch URL
    async with aiohttp.ClientSession() as session:
        result = await calculator(session, stock_list, parameter, tokens, catch_url)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())

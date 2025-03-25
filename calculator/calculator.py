import time
import numpy as np
from datetime import datetime, timedelta

from Database.Goodinfo import Goodinfo
from Database.YahooFinance import YahooFinance
from Database.Anue import ANUE
from utils.Math import Math


class Stock_Predictor:
    def __init__(self, Database, stock_id, parameter, CatchURL):
        self.level, self.year, self.EPS = parameter
        self.stock_id = stock_id
        self.CatchURL = CatchURL

        start_date = (datetime.now() - timedelta(days=self.year * 365)).strftime(
            "%Y-%m-%d"
        )
        Database.stock_id, Database.start_date = stock_id, start_date

        self.StockName = Database.get_stock_info(stock_id, "stock_id", "stock_name")
        self.Market = (
            "TW"
            if Database.get_stock_info(stock_id, "stock_id", "type") == "twse"
            else "TWO"
        )
        self.industry_category = Database.get_stock_info(
            stock_id, "stock_id", "industry_category"
        )

        self.perDatas, self.pbrDatas = Database.get_per_pbr()

        self.priceDatas = Database.get_closing_price()
        self.lastPrice = self.priceDatas[-1][-1]
        self.epsDatas = Database.get_eps()

        goodinfo = Goodinfo(stock_id)
        self.PEG = 0
        self.companyINFO = "goodinfo.CompanyINFO"

        # yahooFinance = YahooFinance(stock_id, self.Market)
        # self.avg1yTargetEst = yahooFinance.get_1yTargetEst()
        self.avg1yTargetEst = 0

        Anue = ANUE(stock_id, self.StockName, CatchURL, self.level)
        self.FactsetData = Anue.FactsetData

    def price_MeanReversion(self, line_num=5):
        return Math.mean_reversion(self.priceDatas, line_num)

    def per_std(self, line_num=5, fig=False):
        return Math.std(self.perDatas, line_num, fig)

    def per_quartile(self):
        return Math.quartile(self.perDatas)

    def pbr_std(self, line_num=5, fig=False):
        return Math.std(self.pbrDatas, line_num, fig)

    def pbr_quartile(self):
        return Math.quartile(self.pbrDatas)


def calculator(Database, StockList, parameter, CatchURL={}):
    StockData = {}
    for i, stock_id in enumerate(StockList, start=1):
        No = i
        print(f"{No} / {len(StockList)}")

        Database.Login()
        Stock_item = Stock_Predictor(Database, stock_id, parameter, CatchURL)

        StockData[stock_id] = {
            "名稱": Stock_item.StockName,
            "代號": stock_id,
            "產業": Stock_item.industry_category,
            "資訊": Stock_item.companyINFO,
            "交易所": Stock_item.Market,
            "價格": Stock_item.lastPrice,
            "EPS(TTM)": sum(Stock_item.epsDatas[-4:]),
            "BPS": Stock_item.lastPrice / Stock_item.pbrDatas[-1],
            "PE(TTM)": Stock_item.perDatas[-1],
            "PB(TTM)": Stock_item.pbrDatas[-1],
            "Yahoo_1yTargetEst": Stock_item.avg1yTargetEst,
        }

        # =======================================================================

        # 從 鉅亨網 取得預估eps及市場預估價，若沒資料則使用近幾季eps
        FactsetESTprice, ESTeps, AnueDataTime, url = Stock_item.FactsetData

        # 市場預估價
        StockData[stock_id]["Anue"] = {
            "EPS(EST)": ESTeps,
            "PE(EST)": (Stock_item.lastPrice / ESTeps) if ESTeps else None,
            "Factest目標價": FactsetESTprice,
            "資料時間": str(AnueDataTime).split(" ")[0].replace("-", "/"),
            "ANUEurl": url,
        }

        # =======================================================================

        # 使用均值回歸預測價格

        StockData[stock_id]["MeanReversion"] = Stock_item.price_MeanReversion()

        # =======================================================================

        # 使用本益比四分位數預測股價

        StockData[stock_id]["ESTPER"] = Stock_item.per_quartile()

        # =======================================================================

        # 利用本益比標準差預測股價
        (df, comp_list) = Stock_item.per_std(fig=False)
        StockData[stock_id]["SDESTPER"] = [df[title][-1] for title in comp_list]

        # =======================================================================

        # 使用股價淨值比四分位數預測股價
        StockData[stock_id]["ESTPBR"] = Stock_item.pbr_quartile()

        # =======================================================================

        # 利用股價淨值比標準差預測股價
        (df, comp_list) = Stock_item.pbr_std(fig=False)
        StockData[stock_id]["SDESTPBR"] = [df[title][-1] for title in comp_list]

        # =======================================================================

        # 從 Goodinfo 取得 PEG
        StockData[stock_id]["PEG"] = Stock_item.PEG

        # =======================================================================

        time.sleep(1)
        # print(StockData[stock_id])
    return StockData

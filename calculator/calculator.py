import os
import sys
import time
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(__file__) + "/..")

from Database.Goodinfo import Goodinfo
from Database.YahooFinance import YahooFinance
from Database.Anue import ANUE
from utils.Math import Math

from utils.utils import logger


QUARTILE_TITLES = ["25%", "50%", "75%", "平均"]
MEAN_REVERSION_TITLES = {
                        "prob":       ["往上機率", "區間震盪機率", "往下機率"],
                        "TL":         ["TL價"], 
                        "expect":     ["保守做多期望值", "樂觀做多期望值", "樂觀做空期望值"], 
                        "targetprice":["超極樂觀", "極樂觀", "樂觀", "趨勢", "悲觀", "極悲觀", "超極悲觀"]
                        }

class Stock_Predictor:
    def __init__(self, database, stock_id, parameter, catch_url):
        level, year = parameter
        self.stock_id = stock_id
        self.database = database
        self.catch_url = catch_url

        start_date = (datetime.now() - timedelta(days=year * 365)).strftime("%Y-%m-%d")
        self.database.stock_id, self.database.start_date = stock_id, start_date

        stock_info = self._fetch_stock_info()
        self.stock_name = stock_info["stock_name"]
        self.market = "TW" if stock_info["type"] == "twse" else "TWO"
        self.industry_category = stock_info["industry_category"]

        self.per_datas, self.pbr_datas = self.database.get_per_pbr()
        self.price_datas = self.database.get_closing_price()
        self.last_price = self.price_datas[-1][-1] if self.price_datas else None
        self.eps_datas = self.database.get_eps()

        goodinfo = Goodinfo(stock_id)
        self.peg = goodinfo.TTMPEG
        self.company_info = goodinfo.business

        yahooFinance = YahooFinance(stock_id, self.market)
        self.avg1y_target_est = yahooFinance.get_1y_target_est()

        self.factset_data = ANUE(stock_id, self.stock_name, catch_url, level).FactsetData

    def _fetch_stock_info(self):
        return self.database.get_stock_info(self.stock_id, "stock_id", ["stock_name", "type", "industry_category"])

    def process(self):
        last_price = self.last_price
        eps_data = self.eps_datas
        pbr_data = self.pbr_datas
        per_data = self.per_datas
        
        stock_data = {
            "名稱": self.stock_name,
            "代號": self.stock_id,
            "產業": self.industry_category,
            "資訊": self.company_info,
            "交易所": self.market,
            "價格": last_price,
            "EPS(TTM)": sum(eps_data[-4:]) if eps_data else None,
            "BPS": last_price / pbr_data[-1] if pbr_data else None,
            "PE(TTM)": per_data[-1] if per_data else None,
            "PB(TTM)": pbr_data[-1] if pbr_data else None,
            "Yahoo_1yTargetEst": self.avg1y_target_est,
        }

        # 從 鉅亨網 取得預估eps及市場預估價，若沒資料則使用近幾季eps
        factset_est_price, est_eps, anue_data_time, url = self.factset_data
        stock_data.update(
            {
                "EPS(EST)": est_eps if est_eps else None,
                "PE(EST)": (last_price / est_eps) if est_eps else None,
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
        stock_data.update({f"PE({t})" : df[t][-1] for t in comp_list})

        # 使用股價淨值比四分位數預測股價
        df = Math.quartile(self.pbr_datas)
        stock_data.update({f"PB({t})": d for t, d in zip(QUARTILE_TITLES, df)})

        # 利用股價淨值比標準差預測股價
        df, comp_list = Math.std(self.pbr_datas)
        stock_data.update({f"PB({t})" : df[t][-1] for t in comp_list})

        # 從 Goodinfo 取得 PEG
        stock_data["PEG"] = self.peg

        return stock_data


def calculator(database, stock_list, parameter, catch_url={}):
    stock_datas = {}
    for i, stock_id in enumerate(stock_list, start=1):
        logger.info(f"Processing {i}/{len(stock_list)}: {stock_id}")
        try:
            database.login()
            predictor = Stock_Predictor(database, stock_id, parameter, catch_url)
            stock_datas.update({stock_id:predictor.process()})
        except Exception as e:
            logger.error(f"Error processing {stock_id}: {e}")
    return stock_datas

if __name__ == "__main__":
    from Database.Finmind import Finminder
    from utils.utils import load_token

    token = load_token()
    db = Finminder(token)
    stock_list = ["2330"]  # Example stock list
    parameter = (1, 5)  # Example parameters
    catch_url = {}  # Example catch URL

    result = calculator(db, stock_list, parameter, catch_url)
    print(result)
    
import time
import pytz
import statistics
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression

from calculator.Goodinfo import Goodinfo
from utils.utils import get_search_results, fetch_webpage


class Stock_Predictor:
    def __init__(self, Database, stock, parameter, CatchURL):
        self.str_lst = []
        self.level, self.year, self.EPS = parameter
        now_time = datetime.now()
        interval_time = now_time - timedelta(days=int(self.year * 360))
        self.start_date = interval_time.strftime("%Y-%m-%d")
        self.stock_id, self.stock_name = stock
        self.warn_str = "Warning: These PER is calculated from date {}, you can modify the date to run again.".format(
            self.start_date
        )
        self.CatchURL = CatchURL
        self.Database = Database
        self.Database.stock_id, self.Database.start_date = (
            self.stock_id,
            self.start_date,
        )
        self.per_pbr = self.Database.get_per_pbr()
        self.closing_price = self.Database.get_closing_price()

    def quartile(self, datas):
        lst_data = [np.percentile(datas, p) for p in (25, 50, 75)]
        lst_data.append(round(statistics.mean(datas), 2))
        self.current_pe = datas[-1]
        return np.array(lst_data)

    def mean_reversion(self, line_num=5):

        prob_data = [0.001, 0.021, 0.136, 0.341, 0.341, 0.136, 0.021, 0.001]
        reg = LinearRegression()
        dates, price = self.closing_price

        idx = np.arange(1, len(price) + 1)
        reg.fit(idx.reshape(-1, 1), price)

        # print(reg.coef_[0]) # 斜率
        # print(reg.intercept_) # 截距
        df = {"date": np.array(dates), "TL": reg.intercept_ + idx * reg.coef_[0]}
        df["y-TL"] = price - df["TL"]
        df["SD"] = df["y-TL"].std()
        for i in range(1, 4):
            df[f"TL-{i}SD"] = df["TL"] - i * df["SD"]
            df[f"TL+{i}SD"] = df["TL"] + i * df["SD"]

        df["close"] = np.array(price)
        price_now = df["close"][-1]
        up_prob, hold_prob, down_prob = 0, 0, sum(prob_data)
        comp_list = (
            [f"TL+{i}SD" for i in range(3, 0, -1)]
            + ["TL"]
            + [f"TL-{i}SD" for i in range(1, 4)]
        )
        for idx, item in enumerate(comp_list):
            if price_now < df[item][-1]:
                up_prob += prob_data[idx]
                down_prob -= prob_data[idx]
            else:
                hold_prob += prob_data[idx]
                down_prob -= prob_data[idx]
                break

        TL = df["TL"][-1]
        expect_val_bull_1 = up_prob * (TL - price_now) - down_prob * price_now
        expect_val_bull_2 = up_prob * (TL - price_now) - down_prob * (
            price_now - df["TL-3SD"][-1]
        )
        expect_val_bear_1 = down_prob * (price_now - TL) - up_prob * (
            df["TL+3SD"][-1] - price_now
        )

        MReversion = [
            [
                round(up_prob * 100, 2),
                round(hold_prob * 100, 2),
                round(down_prob * 100, 2),
            ],
            [round(TL, 2), (TL - price_now) / price_now * 100],
            [
                round(expect_val_bull_1, 2),
                round(expect_val_bull_1 / price_now * 100, 2),
            ],
            [
                round(expect_val_bull_2, 2),
                round(expect_val_bull_2 / price_now * 100, 2),
            ],
            [
                round(expect_val_bear_1, 2),
                round(expect_val_bear_1 / price_now * 100, 2),
            ],
        ]

        return price_now, MReversion

    def get_eps(self):
        estprice, eps, DataTime, EPSeveryear, url = self.crwal_estimate_eps()
        # estprice, eps, DataTime, EPSeveryear = -1,None,None,None

        if (datetime.now() - DataTime).days > 365:
            eps = None

        if self.EPS is not None:
            eps = self.EPS

        # 近四季EPS總和
        lst_eps_sum = sum(self.Database.get_eps()[-4:])
        if type(eps) != int and type(eps) != float:
            eps = lst_eps_sum
        return estprice, eps, lst_eps_sum, DataTime, EPSeveryear, url

    def crwal_estimate_eps(self):
        stock_id, StockName = self.stock_id, self.stock_name
        CatchURL = self.CatchURL
        level = self.level
        EPS = None
        estprice = -1
        DataTime = datetime(1970, 1, 1, 0, 0, 0)
        year_str = str(datetime.now().year)
        month_float = float(datetime.now().month)

        # Get the cnyes news
        # search_str = f'factset eps cnyes {stock_id} tw site:news.cnyes.com AND intitle:"{stock_id}" AND intitle:"factset"'
        # search_str = f'"鉅亨速報 - Factset 最新調查："{StockName}({stock_id}-TW)"EPS預估" site:news.cnyes.com'
        search_str = f"鉅亨速報 - Factset 最新調查：{StockName}({stock_id}-TW)EPS預估+site:news.cnyes.com"
        # print(search_str)
        search_results = get_search_results(search_str, 10)
        # print(search_results)

        url_list = [j.replace("print", "id") for j in search_results if "cnyes.com" in j]
        if stock_id in CatchURL and isinstance(CatchURL[stock_id]["url"], str) and CatchURL[stock_id]["url"] not in url_list:
            url_list.append(CatchURL[stock_id]["url"])

        urldata = []
        for url in url_list:
            try:
                soup = fetch_webpage(url)
                webtime = soup.find(class_="alr4vq1").contents[-1]
                webtime = datetime.strptime(webtime, "%Y-%m-%d %H:%M")
                urldata.append({"date": webtime, "url": url})
                # print(webtime, url)
            except:
                continue

        sorted_data = sorted(urldata, key=lambda x: x["date"], reverse=True)
        # print(sorted_data)
        for i, timeurl in enumerate(sorted_data):
            try:
                DataTime, url = timeurl["date"], timeurl["url"]
                print(DataTime, ":", url)
                soup = fetch_webpage(url)
                webtitle = soup.find(id="article-container").text

                if webtitle.split("(")[1].split("-")[0] != str(stock_id):
                    continue

                try:
                    estprice = webtitle.split("預估目標價為")[1].split("元")[0]
                except:
                    pass

                rows = soup.table.find_all("tr")  # 提取表格的行
                headers = [
                    header.get_text(strip=True) for header in rows[0].find_all("td")
                ]  # 提取表頭
                EPSeveryear = [headers]

                # print(headers[0])
                if headers[0] != "預估值":
                    continue

                # 提取每行數據並加入結果列表
                for row in rows[1:]:
                    cells = row.find_all("td")
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    EPSeveryear.append(row_data)

                for idx, s in enumerate(headers):
                    if year_str in s:
                        ThisYearEPSest = float(EPSeveryear[level][idx].split("(")[0])
                        if idx < len(headers) - 1:
                            NextYearEPSest = float(
                                EPSeveryear[level][idx + 1].split("(")[0]
                            )
                            EPS = (((12 - month_float) / 12) * ThisYearEPSest) + (
                                (month_float / 12) * NextYearEPSest
                            )
                        else:
                            EPS = ThisYearEPSest
                        print("\n", stock_id, " ", EPS, ":", DataTime, ":", url)
                        return (float(estprice), EPS, DataTime, EPSeveryear, url)
            except:
                DataTime = datetime(1970, 1, 1, 0, 0, 0)
                continue
        return float(estprice), EPS, DataTime, None, None

    def std(self, dates, datas, line_num=5, fig=False):
        reg = LinearRegression()

        idx = np.arange(1, len(datas) + 1)
        reg.fit(idx.reshape(-1, 1), datas)

        # print(reg.coef_[0]) # 斜率
        # print(reg.intercept_) # 截距
        df = {}
        df = {
            "date": np.array(dates),
            "TL": np.full((len(datas),), statistics.median(datas)),
        }

        df["y-TL"] = datas - df["TL"]
        df["SD"] = df["y-TL"].std()
        for i in range(1, 4):
            df[f"TL-{i}SD"] = df["TL"] - i * df["SD"]
            df[f"TL+{i}SD"] = df["TL"] + i * df["SD"]
        df["datas"] = np.array(datas)
        comp_list = (
            [f"TL+{i}SD" for i in range(3, 0, -1)]
            + ["TL"]
            + [f"TL-{i}SD" for i in range(1, 4)]
        )

        return (df, comp_list)

    def per_std(self, line_num=5, fig=False):
        return self.std(self.per_pbr["date"], self.per_pbr["PER"], line_num, fig)

    def per_quartile(self):
        return self.quartile(self.per_pbr["PER"])

    def pbr_std(self, line_num=5, fig=False):
        return self.std(self.per_pbr["date"], self.per_pbr["PBR"], line_num, fig)

    def pbr_quartile(self):
        return self.quartile(self.per_pbr["PBR"])

    def get_BVPS(self):
        return self.price_now / self.per_pbr["PBR"][-1]


def calculator(Database, StockList, EPSLists, parameter, CatchURL={}):
    StockData = {"parameter": parameter}
    year = parameter[2]
    taiwan_tz = pytz.timezone("Asia/Taipei")
    taiwan_time = datetime.now(taiwan_tz)
    for i, stock_id in enumerate(StockList, start=1):
        No = i
        print(f"{No} / {len(StockList)}")

        Database.Login()

        # 股票基本資訊
        StockName = Database.get_stock_info(stock_id, "stock_id", "stock_name")
        IPOtype = Database.get_stock_info(stock_id, "stock_id", "type")
        industry_category = Database.get_stock_info(
            stock_id, "stock_id", "industry_category"
        )
        Stock_item = Stock_Predictor(
            Database, [stock_id, StockName], parameter, CatchURL
        )

        StockData[stock_id] = {
            "Name": StockName,
            "stock_id": stock_id,
            "IPOtype": IPOtype,
            "industry_category": industry_category,
            "getTime": taiwan_time,
        }
        # Usage: stock_id, years
        # 使用均值回歸預測價格

        price_now, MReversion = Stock_item.mean_reversion()
        Stock_item.price_now = price_now

        StockData[stock_id]["mean_reversion"] = MReversion
        # =======================================================================

        # 從 鉅亨網 取得預估eps及市場預估價，若沒資料則使用近幾季eps，或使用自己輸入的
        if EPSLists and EPSLists[No - 1]:
            Stock_item.EPS = float(EPSLists[No - 1])

        FactsetESTprice, ESTeps, lst_eps_sum, AnueDataTime, EPSeveryear, url = (
            Stock_item.get_eps()
        )

        StockData[stock_id].update(
            {"price": price_now, "EPSeveryear": EPSeveryear},
        )

        # 市場預估價
        StockData[stock_id]["Anue"] = {
            "DataTime": str(AnueDataTime).split(" ")[0].replace("-", "/"),
            "FactsetESTprice": [
                FactsetESTprice,
                (FactsetESTprice - price_now) / price_now * 100,
            ],
            "ESTeps": ESTeps,
            "FuturePER": price_now / ESTeps,
            "url": url,
        }
        # =======================================================================

        # Usage:   'api', stock_id, ESTeps, year_number
        # 使用本益比四分位數預測股價

        pe_list = Stock_item.per_quartile()

        StockData[stock_id]["ESTPER"] = []
        for i in range(4):
            PE, Price = pe_list[i], ESTeps * pe_list[i]
            Rate = (Price / price_now - 1) * 100
            StockData[stock_id]["ESTPER"].append([PE, Price, Rate])
        # =======================================================================

        # Usage: stock_id, ESTeps, year
        # 利用本益比標準差預測股價

        (df, comp_list) = Stock_item.per_std(fig=False)
        StockData[stock_id]["SDESTPER"] = []
        for i, title in enumerate(comp_list):
            PE, Price = df[title][-1], ESTeps * df[title][-1]
            Rate = (Price / price_now - 1) * 100
            StockData[stock_id]["SDESTPER"].append([PE, Price, Rate])
        # =======================================================================

        # Usage:   'api', stock_id, BVPS, year_number
        # 使用股價淨值比四分位數預測股價
        BVPS = Stock_item.get_BVPS()
        pe_list = Stock_item.pbr_quartile()

        StockData[stock_id]["ESTPBR"] = []
        for i in range(4):
            PE, Price = pe_list[i], BVPS * pe_list[i]
            Rate = (Price / price_now - 1) * 100
            StockData[stock_id]["ESTPBR"].append([PE, Price, Rate])
        # =======================================================================

        # Usage: stock_id, ESTeps, year
        # 利用股價淨值比標準差預測股價

        (df, comp_list) = Stock_item.pbr_std(fig=False)
        StockData[stock_id]["SDESTPBR"] = []
        for i, title in enumerate(comp_list):
            PE, Price = df[title][-1], BVPS * df[title][-1]
            Rate = (Price / price_now - 1) * 100
            StockData[stock_id]["SDESTPBR"].append([PE, Price, Rate])
        # =======================================================================
        # 從 Goodinfo 取得 PEG 和 公司資訊
        try:
            peg = Stock_item.per_pbr["PER"][-1] / (ESTeps / lst_eps_sum - 1) / 100
        except:
            peg = Goodinfo.get_peg(stock_id)

        StockData[stock_id]["PEG"] = (
            [peg, price_now / peg / ESTeps, price_now / peg, (1 / peg - 1) * 100]
            if peg
            else [-999, -999, -999, -999]
        )
        StockData[stock_id]["companyinfo"] = Goodinfo.get_company_info(stock_id)
        # time.sleep(5)
    return StockData

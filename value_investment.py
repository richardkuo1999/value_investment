import sys
import csv
import signal
import datetime
import tkinter as tk
import numpy as np
import statistics
from termcolor import *
from FinMind.data import DataLoader
import os
import time
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import urllib.request
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates  # 處理日期
import pandas as pd
from sklearn import linear_model
import plotly.graph_objects as go
from enum import Enum
from bs4 import BeautifulSoup

from stock_selector.stock_select import getETFConstituent, getInstitutional_TOP50

fw = None
csvfile = None
finmind_token = ""

with open("token.txt", "r") as f:
    finmind_token = f.read()

api = DataLoader()
api.login_by_token(api_token=finmind_token)
all_stock_info = api.taiwan_stock_info()


class Future(Enum):
    NOW = 0
    NEXT = 1
    LATER = 2


class Msg(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CIRITCAL = 4


def msg_show(level, msg):
    updated_msg = ""
    level_list = ["DEBUG: ", "INFO: ", "WARNING: ", "ERROR: ", "CRITICAL: "]
    for i in Msg:
        if level == i:
            updated_msg = level_list[i.value] + msg
            break
    print(updated_msg)


def Printf(msg, file=None):
    if file:
        print(msg, file=file)
    print(msg)


def Check_api_request_limit():
    resp = requests.get(
        "https://api.web.finmindtrade.com/v2/user_info", params={"token": finmind_token}
    )
    api_request_limit = resp.json()["api_request_limit"]
    user_count = resp.json()["user_count"]
    if (api_request_limit - user_count) <= 10:
        print(f"user_count/api_request_limit: {user_count}/{api_request_limit}")
        time.sleep(600)


class Stock_Predictor:
    def __init__(self, api, sn, eps, interval):
        self.api = api
        now_time = datetime.datetime.now()
        interval_day = interval
        interval_day *= 360
        self.str_lst = []
        interval_time = now_time - datetime.timedelta(days=int(interval_day))
        self.start_date = interval_time.strftime("%Y-%m-%d")
        self.stock_number = sn
        self.eps = eps
        self.warn_str = "Warning: These PER is calculated from date {}, you can modify the date to run again.".format(
            self.start_date
        )
        self.get_warning()

    def get_warning(self):
        bar = "=" * (len(self.warn_str) // 4)
        self.str_lst.append(bar)
        self.str_lst.append("={}=".format(self.warn_str))
        self.str_lst.append(bar)

    def get_PER(self):
        lst_per = []
        df = self.api.taiwan_stock_per_pbr(
            stock_id=str(self.stock_number), start_date=self.start_date
        )
        data = df["PER"]
        lst_per = [
            np.percentile(data, (25)),
            np.percentile(data, (50)),
            np.percentile(data, (75)),
            round(statistics.mean(data), 2),
        ]
        self.current_pe = data.values.tolist()[-1]
        return np.array(lst_per)


def plotly_figure(sn, df, line_num):
    fig = go.Figure()
    line_list = ["TL+2SD", "TL+SD", "TL", "TL-SD", "TL-2SD", "close"]
    if line_num == 7:
        line_list.insert(-1, "TL-3SD")
        line_list.insert(0, "TL+3SD")

    for i in line_list:
        fig.add_trace(go.Scatter(x=df["date"], y=df[i], name=i))
    fig.update_layout(
        xaxis_title="Dates",
        yaxis_title="Price",
        font=dict(family="Courier New, monospace", size=26, color="#7f7f7f"),
        title={"text": sn, "xanchor": "center", "y": 0.995, "x": 0.5, "yanchor": "top"},
    )
    fig.update(layout_showlegend=False)
    fig.show()


def plotly_figure_pe(sn, df, line_num):
    fig = go.Figure()
    line_list = ["TL+2SD", "TL+SD", "TL", "TL-SD", "TL-2SD", "PER"]
    if line_num == 7:
        line_list.insert(-1, "TL-3SD")
        line_list.insert(0, "TL+3SD")

    for i in line_list:
        fig.add_trace(go.Scatter(x=df["date"], y=df[i], name=i))
    fig.update_layout(
        xaxis_title="Dates",
        yaxis_title="PE",
        font=dict(family="Courier New, monospace", size=26, color="#7f7f7f"),
        title={"text": sn, "xanchor": "center", "y": 0.995, "x": 0.5, "yanchor": "top"},
    )
    fig.update(layout_showlegend=False)
    fig.show()


def mean_reversion(sn, years, line_num=5):

    prob_data = [0.001, 0.021, 0.136, 0.341, 0.341, 0.136, 0.021, 0.001]
    now_time = datetime.datetime.now()
    interval_time = now_time - datetime.timedelta(days=int(years * 365))
    date_str = interval_time.strftime("%Y-%m-%d")
    reg = linear_model.LinearRegression()
    df = {}
    stock_data = api.taiwan_stock_daily(stock_id=sn, start_date=date_str)
    data = stock_data["close"].values.tolist()
    dates = stock_data["date"].values.tolist()

    for e1, e2 in zip(data, dates):
        if e1 == 0:
            data.remove(e1)
            dates.remove(e2)

    idx = np.array([i for i in range(1, len(data) + 1)])
    reg.fit(idx.reshape(-1, 1), data)

    # print(reg.coef_[0]) # 斜率
    # print(reg.intercept_) # 截距
    df["date"] = np.array(dates)
    df["TL"] = reg.intercept_ + idx * reg.coef_[0]
    df["y-TL"] = data - df["TL"]
    df["SD"] = df["y-TL"].std()
    df["TL-3SD"] = df["TL"] - 3 * df["SD"]
    df["TL-2SD"] = df["TL"] - 2 * df["SD"]
    df["TL-SD"] = df["TL"] - df["SD"]

    df["TL+3SD"] = df["TL"] + 3 * df["SD"]
    df["TL+2SD"] = df["TL"] + 2 * df["SD"]
    df["TL+SD"] = df["TL"] + df["SD"]
    df["close"] = np.array(data)
    price_now = df["close"][-1]
    up_prob = 0
    hold_prob = 0
    stock_range = []
    text_list = []
    down_prob = sum(prob_data)
    comp_list = ["TL+3SD", "TL+2SD", "TL+SD", "TL", "TL-SD", "TL-2SD", "TL-3SD"]
    for idx, item in enumerate(comp_list):
        comp_data = df[item][-1]
        if price_now < comp_data:
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
    text_list.append(
        [
            Msg.WARNING,
            "均值回歸適合使用在穩定成長的股票上，如大盤or台積電等，高速成長及景氣循環股不適用，請小心服用。",
        ]
    )
    text_list.append([Msg.WARNING, "偏離越多標準差越遠代表趨勢越強，請勿直接進場。"])
    text_list.append(
        [
            Msg.INFO,
            "{} 往上的機率為: {}%, 維持在這個區間的機率為: {}%, 往下的機率為: {}%".format(
                sn,
                round(up_prob * 100, 2),
                round(hold_prob * 100, 2),
                round(down_prob * 100, 2),
            ),
        ]
    )
    text_list.append(
        [Msg.INFO, "目前股價: {}, TL價: {}".format(price_now, round(TL, 2))]
    )

    text_list.append([Msg.INFO, "做多評估："])
    text_list.append(
        [
            Msg.INFO,
            "期望值為: {}, 期望報酬率為: {}% (保守計算: 上檔TL，下檔歸零)".format(
                round(expect_val_bull_1, 2),
                round(expect_val_bull_1 / price_now * 100, 2),
            ),
        ]
    )
    text_list.append(
        [
            Msg.INFO,
            "期望值為: {}, 期望報酬率為: {}% (樂觀計算: 上檔TL，下檔-3SD)".format(
                round(expect_val_bull_2, 2),
                round(expect_val_bull_2 / price_now * 100, 2),
            ),
        ]
    )

    text_list.append([Msg.INFO, "做空評估: "])
    text_list.append(
        [
            Msg.INFO,
            "期望值為: {}, 期望報酬率為: {}% (樂觀計算: 上檔+3SD，下檔TL)".format(
                round(expect_val_bear_1, 2),
                round(expect_val_bear_1 / price_now * 100, 2),
            ),
        ]
    )
    for l in text_list:
        Printf(l, file=fw)
    # plotly_figure(sn, df, line_num)
    return price_now


def per_std(sn, eps, years, line_num=5, fig=False):
    now_time = datetime.datetime.now()
    interval_time = now_time - datetime.timedelta(days=int(years * 365))
    date_str = interval_time.strftime("%Y-%m-%d")
    reg = linear_model.LinearRegression()
    stock_data = api.taiwan_stock_per_pbr(stock_id=str(sn), start_date=date_str)
    data = stock_data["PER"].values.tolist()
    dates = stock_data["date"].values.tolist()

    for e1, e2 in zip(data, dates):
        if e1 == 0:
            data.remove(e1)
            dates.remove(e2)

    idx = np.array([i for i in range(1, len(data) + 1)])
    reg.fit(idx.reshape(-1, 1), data)

    # print(reg.coef_[0]) # 斜率
    # print(reg.intercept_) # 截距
    df = {}
    df["date"] = np.array(dates)
    # df['TL'] = reg.intercept_ +idx * reg.coef_[0]
    # middle = sum(data) / len(data)
    middle = statistics.median(data)
    df["TL"] = np.full((len(data),), middle)
    df["y-TL"] = data - df["TL"]
    df["SD"] = df["y-TL"].std()
    df["TL-3SD"] = df["TL"] - 3 * df["SD"]
    df["TL-2SD"] = df["TL"] - 2 * df["SD"]
    df["TL-SD"] = df["TL"] - df["SD"]

    df["TL+3SD"] = df["TL"] + 3 * df["SD"]
    df["TL+2SD"] = df["TL"] + 2 * df["SD"]
    df["TL+SD"] = df["TL"] + df["SD"]

    df["PER"] = np.array(data)

    comp_list = ["TL+3SD", "TL+2SD", "TL+SD", "TL", "TL-SD", "TL-2SD", "TL-3SD"]

    if fig:
        plotly_figure_pe(sn, df, line_num)

    return (df, comp_list)


def handler(signum, frame):
    raise Exception("Timeout!")


# signal.signal(signal.SIGALRM, handler)
# signal.alarm(10)


def crwal_estimate_eps(sn, level, offset):
    from googlesearch import search

    search_str = "factset eps cnyes {} tw".format(sn)
    # print(search_str)
    for j in search(search_str, stop=5, pause=2.0):
        url = j
        # print(url)
        if "cnyes" not in url:
            continue

        result = requests.get(url)
        soup = BeautifulSoup(result.text, "html.parser")

        try:
            if str(
                soup.find(attrs={"data-ga-click-item": True}).text.split("-")[0]
            ) != str(sn):
                continue

            data = soup.table.get_text().split()

            row_len = len(soup.table.tr.get_text().split())
            res = []
            for i in range(5):
                res.append(data[i * row_len : (i + 1) * row_len])
                Printf(res[-1], file=fw)

            eps_title = res[0]
            year_str = str(datetime.date.today().year + offset)
            for idx, s in enumerate(eps_title):
                if year_str in s:
                    offset = idx
                    break
            targ_eps = res[level]
            Printf(targ_eps, file=fw)
            nums = targ_eps[int(offset)]
            numsm1 = targ_eps[int(offset) - 1]

            return (float(nums.split("(")[0]) + float(numsm1.split("(")[0])) / 2
            # return ( float(nums.split("(")[0]) )

        except:
            continue
    return None


def get_EPS(sn):
    # 近四季EPS總和
    df = api.taiwan_stock_financial_statement(
        stock_id=str(sn),
        start_date="2019-01-01",
    )
    lst = df[df.type == "EPS"].values.tolist()
    last_date = lst[-1][0]
    lst_eps = [ll[3] for ll in lst]
    return sum(lst_eps[-4:])


def calculator(
    stock_number, year, sel=1, level=4, EPS=None, csvwriter=None, No=0, isOTC=False
):
    csvdata = [None] * 38
    StockName = all_stock_info.loc[
        all_stock_info["stock_id"] == str(stock_number)
    ].iloc[0]["stock_name"]
    Printf(f"股票名稱: {StockName}", file=fw)
    csvdata[0], csvdata[1], csvdata[2] = (
        StockName,
        str(stock_number),
        f'=STOCK(CONCAT(B{No+1},"{".two" if isOTC else ".tw"}"))',
    )
    split_str = "=" * 100
    """
  parameter -> sel
  # 0: 今年
  # 1: 明年
  # 2: 後年
  """
    """
  parameter -> level
  # 1: high, 2: low, 3: average, 4: medium
  """
    eps = crwal_estimate_eps(stock_number, level, sel)
    if type(eps) != int and type(eps) != float:
        Printf("[ WRRNING ] 無法取得 Fectset EPS 評估報告，使用近四季EPS總和.", file=fw)
        eps = get_EPS(stock_number) if EPS is None else EPS

    Printf(split_str, file=fw)
    Printf(
        "股票代號:\t{},\t\t估計EPS:\t{},\t\t歷史本益比參考年數:\t{}".format(
            stock_number, eps, year
        ),
        file=fw,
    )
    csvdata[3], csvdata[4] = str(eps), str(year)
    Printf(split_str, file=fw)
    # Usage: stock_number, years

    Printf("計算股價均值回歸......\n", file=fw)
    price_now = mean_reversion(stock_number, year)
    Printf("\n現在股價為:\t{:.2f}".format(price_now), file=fw)
    Printf("未來本益比為:\t{:.2f}".format(price_now / eps), file=fw)

    PE = None
    # Usage:   'api', stock_number, eps, year_number
    PER = Stock_Predictor(api, stock_number, eps, year)
    if PER:
        pe_list = PER.get_PER()
        pe_rate = 25

        # printf("目前本益比為:\t{}".format(PE.current_pe))
        Printf(split_str, file=fw)
        Printf("計算本益比四分位數與平均本益比......\n", file=fw)
        uniformat = (
            "本益比{}% 為:\t{:<20.2f} 推算價位為:\t{:<20.2f} 推算潛在漲幅為:\t{:.2f}%"
        )
        for i in range(3):
            PE, Price, Rate = (
                pe_list[i],
                eps * pe_list[i],
                (eps * pe_list[i] - price_now) / price_now * 100,
            )
            Printf(uniformat.format(pe_rate * (i + 1), PE, Price, Rate), file=fw)
            csvdata[5 + i * 3], csvdata[6 + i * 3], csvdata[7 + i * 3] = (
                str(PE),
                str(Price),
                f"=({Price} - C{No+1}) / C{No+1} * 100",
            )
        uniformat = (
            "本益比平均為:\t{:<20.2f} 推算價位為:\t{:<20.2f} 推算潛在漲幅為:\t{:.2f}%"
        )
        PE, Price = pe_list[-1], eps * pe_list[-1]
        Printf(
            uniformat.format(PE, Price, (Price - price_now) / price_now * 100), file=fw
        )
        csvdata[14], csvdata[15], csvdata[16] = (
            str(PE),
            str(Price),
            f"=({Price} - C{No+1}) / C{No+1} * 100",
        )
    # Usage: stock_number, eps, year
    Printf(split_str, file=fw)
    uniformat = "{:<20} {:<20.2f} 推算價位為:\t{:<20.2f} 推算潛在漲幅為:\t{:.2f}%"
    Printf("計算本益比標準差......\n", file=fw)
    (df, comp_list) = per_std(stock_number, eps, year, fig=False)
    for i, title in enumerate(comp_list):
        PE, Price = df[title][-1], eps * df[title][-1]
        Printf(
            uniformat.format(title, PE, Price, (Price - price_now) / price_now * 100),
            file=fw,
        )
        csvdata[17 + i * 3], csvdata[18 + i * 3], csvdata[19 + i * 3] = (
            str(PE),
            str(Price),
            f"=({Price} - C{No+1}) / C{No+1} * 100",
        )
    if csvwriter:
        csvwriter.writerow(csvdata)


def stock_select(etf_id, e_eps=None, csvwriter=None, Hot=None):

    url_template = "https://www.moneydj.com/ETF/X/Basic/Basic0007A.xdjhtm?etfid={}.TW"

    # 外資買賣超、投信買賣超、公股銀行買賣超
    buy_list = [
        "https://histock.tw/stock/three.aspx?s=b",
        "https://histock.tw/stock/three.aspx?s=c",
        "https://histock.tw/stock/broker8.aspx",
    ]
    stock_list = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
    }

    url = url_template.format(etf_id)

    result = requests.get(url, headers=headers)
    result.encoding = "utf-8"
    soup = BeautifulSoup(result.text, "html5lib")
    data = soup.find_all("td", class_="col05")
    for idx, name in enumerate(data):
        stock_list.append(name.text)

    if Hot:
        for idx, link in enumerate(buy_list):
            url = link
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
            }
            result = requests.get(url, headers=headers)
            result.encoding = "utf-8"
            soup = BeautifulSoup(result.text, "html5lib")
            data = []
            if idx == 2:
                data = soup.find_all("span", class_="w100 name")
            else:
                data = soup.find_all("span", class_="w58 name")

            for idx_data, name in enumerate(data):
                txt = name.text
                if idx == 2:
                    txt = txt[1:]
                stock_list.append(txt)

    stock_list = list(set(stock_list))
    stock_dict = {}
    print(stock_list)
    for sn in stock_list:
        try:
            stock_id = all_stock_info.loc[all_stock_info["stock_name"] == sn].iloc[0][
                "stock_id"
            ]
            if len(stock_id) < 5:
                stock_dict[sn] = stock_id
        except:
            pass

    year = 5.5
    sel = 1
    level = 4
    for i, (sn, stock_id) in enumerate(stock_dict.items(), start=1):
        Check_api_request_limit()
        Printf("*" * 50, file=fw)
        Printf(f"{i}. {sn, stock_id}", file=fw)
        calculator(
            stock_id, year, sel, level, e_eps, csvwriter, i, (etf_id == "006201")
        )
        time.sleep(5)


def ResultOutput(title, StockList):
    fw = open(f"results/{title}.txt", "w")
    csvfile = open(f"results/{title}.csv", "w", newline="", encoding="utf-8")
    csvwriter = csv.writer(csvfile, delimiter=",")
    csvwriter.writerow(
        [
            "股票名稱",
            "股票代號",
            "昨日價格",
            "估計EPS",
            "歷史PE參考年數目",
            "PE25%",
            "PE25%價位",
            "PE25%潛在漲幅",
            "PE50%",
            "PE50%價位",
            "PE50%潛在漲幅",
            "PE75%",
            "PE75%價位",
            "PE75%潛在漲幅",
            "PE平均",
            "PE平均價位",
            "PE平均潛在漲幅",
            "TL+3SD PE",
            "TL+3SD價位",
            "TL+3SD在漲幅",
            "TL+2SD PE",
            "TL+2SD價位",
            "TL+2SD在漲幅",
            "TL+SD PE",
            "TL+SD價位",
            "TL+SD潛在漲幅",
            "TL PE",
            "TL價位",
            "TL潛在漲幅",
            "TL-SD PE",
            "TLL-SD價位",
            "TLL-SD潛在漲幅",
            "TL-2SD PE",
            "TL-2SD價位",
            "TL-2SD潛在漲幅",
            "TL-3SD PE",
            "T-3SD價位",
            "TL-3SD潛在漲幅",
        ]
    )
    return fw, csvwriter, csvfile


sel = 1
level = 4
year = 4.5
e_eps = None

if __name__ == "__main__":
    if os.path.exists("results"):
        os.remove("results")
    os.mkdir("results")

    while True:
        UserInput = input(
            "1.查詢ETF成分股\n2. 查詢個股\n3.三大法人買賣超\n4. 退出\n輸入: "
        )
        StockLists = {}

        # 1. 查詢ETF成分股
        if UserInput == "1":
            UserInput = input("1.0050, 0051, 006201\n2. 自行輸入\n輸入: ")
            ETFList = []
            if UserInput == "1":
                ETFList = ["0050", "0051", "006201"]
            elif UserInput == "2":
                ETFList = input("請用空格隔開: ").split(" ")
            for ETF in ETFList:
                StockLists[ETF] = getETFConstituent(ETF)

        # 2. 查詢個股
        elif UserInput == "2":
            StockLists = {"User_Choice": input("請用空格隔開: ").split(" ")}

        # 3.三大法人買賣超
        elif UserInput == "4":
            StockLists = {" Institutional_Investors": getInstitutional_TOP50()}

        # 4. 退出
        elif UserInput == "4":
            break

        else:
            print("Enter Error!!")
            continue
        for title, StockList in StockLists.items():
            print(title, StockList)
            fw, cw, csvfile = ResultOutput(title)

            # Get Data
            calculator(StockList, year, sel, level, e_eps)

            fw.close()
            csvfile.close()
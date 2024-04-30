import time
import datetime
import requests
import statistics
import numpy as np
from bs4 import BeautifulSoup
from googlesearch import search
from sklearn import linear_model

from utils.utils import plotly_figure, Printf, Msg


def Check_api_request_limit(finmind_token):
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


def mean_reversion(api, sn, years, fw=None, line_num=5):

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
    # plotly_figure(sn, df, line_num, "close")
    return price_now


def per_std(api, sn, eps, years, line_num=5, fig=False):
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
        plotly_figure(sn, df, line_num, "PER")

    return (df, comp_list)


"""
parameter -> sel
# 0: 今年
# 1: 明年
# 2: 後年

parameter -> level
# 1: high, 2: low, 3: average, 4: medium
"""


def crwal_estimate_eps(sn, level, offset, fw=None):
    EPS = None
    search_str = "factset eps cnyes {} tw".format(sn)
    # print(search_str)
    url_list = {}
    for j in search(search_str, stop=5, pause=2.0):
        url = j
        # print(url)
        if "cnyes" not in url:
            continue
        url_list[int(url.split('/')[-1])] = url

    url_list = [url_list[key] for key in sorted(url_list, key=lambda x: url_list[x], reverse=True)]
    # print(url_list)

    for url in url_list:
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
            if(data[0] != "預估值"):
                continue
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

            EPS = (float(nums.split("(")[0]) + float(numsm1.split("(")[0])) / 2
            break

        except:
            continue
    return EPS


def get_EPS(api, stock_id, level, sel, EPS=None, fw=None):

    eps = crwal_estimate_eps(stock_id, level, sel, fw)

    if type(eps) != int and type(eps) != float:
        Printf("[ WRRNING ] 無法取得 Fectset EPS 評估報告，使用近四季EPS總和.", file=fw)
        if EPS is not None:
            eps = EPS
        else:
            # 近四季EPS總和
            df = api.taiwan_stock_financial_statement(
                stock_id=stock_id,
                start_date="2019-01-01",
            )
            lst = df[df.type == "EPS"].values.tolist()
            last_date = lst[-1][0]
            lst_eps = [ll[3] for ll in lst]
            eps = sum(lst_eps[-4:])

    return eps


def calculator(
    finmind_token,
    api,
    all_stock_info,
    StockList,
    year=4.5,
    sel=1,
    level=4,
    EPS=None,
    fw=None,
    cw=None,
):

    split_str = "=" * 100
    for i, stock_id in enumerate(StockList, start=1):
        No = i
        Check_api_request_limit(finmind_token)
        Printf(split_str, file=fw)
        print(f'{No}/{len(StockList)}')
        
        csvdata = [None] * 38
        StockName = all_stock_info.loc[
            all_stock_info["stock_id"] == stock_id
        ].iloc[0]["stock_name"]
        Printf(f"股票名稱: {StockName}", file=fw)
        type = all_stock_info.loc[all_stock_info["stock_id"] == stock_id].iloc[0]["type"]
        csvdata[0], csvdata[1], csvdata[2] = (
            StockName,
            str(stock_id),
            f'=STOCK(CONCAT(B{No+1},"{".two" if type=="tpex" else ".tw"}"))',
        )

        eps = get_EPS(api, stock_id, level, sel, EPS, fw)

        Printf(split_str, file=fw)
        Printf(
            "股票代號:\t{},\t\t估計EPS:\t{},\t\t歷史本益比參考年數:\t{}".format(
                stock_id, eps, year
            ),
            file=fw,
        )
        csvdata[3], csvdata[4] = str(eps), str(year)
        Printf(split_str, file=fw)
        # Usage: stock_number, years

        Printf("計算股價均值回歸......\n", file=fw)
        price_now = mean_reversion(api, stock_id, year, fw)
        Printf("\n現在股價為:\t{:.2f}".format(price_now), file=fw)
        Printf("未來本益比為:\t{:.2f}".format(price_now / eps), file=fw)

        PE = None
        # Usage:   'api', stock_number, eps, year_number
        PER = Stock_Predictor(api, stock_id, eps, year)
        if PER:
            pe_list = PER.get_PER()
            pe_rate = 25

            # printf("目前本益比為:\t{}".format(PE.current_pe))
            Printf(split_str, file=fw)
            Printf("計算本益比四分位數與平均本益比......\n", file=fw)
            uniformat = "本益比{}% 為:\t{:<20.2f} 推算價位為:\t{:<20.2f} 推算潛在漲幅為:\t{:.2f}%"
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
            uniformat = "本益比平均為:\t{:<20.2f} 推算價位為:\t{:<20.2f} 推算潛在漲幅為:\t{:.2f}%"
            PE, Price = pe_list[-1], eps * pe_list[-1]
            Printf(
                uniformat.format(PE, Price, (Price - price_now) / price_now * 100),
                file=fw,
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
        (df, comp_list) = per_std(api, stock_id, eps, year, fig=False)
        for i, title in enumerate(comp_list):
            PE, Price = df[title][-1], eps * df[title][-1]
            Printf(
                uniformat.format(
                    title, PE, Price, (Price - price_now) / price_now * 100
                ),
                file=fw,
            )
            csvdata[17 + i * 3], csvdata[18 + i * 3], csvdata[19 + i * 3] = (
                str(PE),
                str(Price),
                f"=({Price} - C{No+1}) / C{No+1} * 100",
            )
        if cw:
            cw.writerow(csvdata)

        time.sleep(5)




if __name__ == "__main__":
    for sn in ([2330]*10):
        eps = crwal_estimate_eps(sn, 4, 1, fw=None)
        print(eps)
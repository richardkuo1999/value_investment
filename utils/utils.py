import os
import csv
import requests
import pandas as pd
from enum import Enum
from pathlib import Path
from bs4 import BeautifulSoup
from googlesearch import search
import plotly.graph_objects as go


def txt_read(file: Path) -> str:
    txtdata = file.read_text()
    return txtdata


default_Parameter = [1, 3, 4.5, None]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
}


def write2txt(msg, file=None):
    if file:
        print(msg, file=file)
    print(msg)


"""
parameter -> y_label
  # close
  # PER
"""


def plotly_figure(sn, df, line_num, y_label):
    fig = go.Figure()
    line_list = ["TL+2SD", "TL+SD", "TL", "TL-SD", "TL-2SD", y_label]
    if line_num == 7:
        line_list.insert(-1, "TL-3SD")
        line_list.insert(0, "TL+3SD")

    for i in line_list:
        fig.add_trace(go.Scatter(x=df["date"], y=df[i], name=i))

    y_axis_title = "Price" if y_label != "PER" else "PE"
    fig.update_layout(
        xaxis_title="Dates",
        yaxis_title=y_axis_title,
        font=dict(family="Courier New, monospace", size=26, color="#7f7f7f"),
        title={"text": sn, "xanchor": "center", "y": 0.995, "x": 0.5, "yanchor": "top"},
    )
    fig.update_layout(showlegend=False)
    fig.show()


def ResultOutput(result_path, title):
    rowtitle = [
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
        "市場預估價",
        "市場預估價潛在漲幅",
        "未來本益比為",
        "資料時間",
    ]
    fw = open(result_path / f"{title}.txt", "w")

    # apple
    apple_csvfile = open(
        result_path / f"Apple_{title}.csv", "w", newline="", encoding="utf-8"
    )
    apple_csvwriter = csv.writer(apple_csvfile, delimiter=",")
    apple_csvwriter.writerow(rowtitle)
    # google
    google_csvfile = open(
        result_path / f"google_{title}.csv", "w", newline="", encoding="utf-8"
    )
    google_csvwriter = csv.writer(google_csvfile, delimiter=",")
    google_csvwriter.writerow(rowtitle)

    return fw, [apple_csvwriter, google_csvwriter], [apple_csvfile, google_csvfile]


def get_google_search_results(query, num_results=10):
    results = []
    # url = f"https://www.google.com/search?q={query}&num={num_results}"
    # response = requests.get(url, headers=headers)
    # if response.status_code == 200:
    #     soup = BeautifulSoup(response.text, "html.parser")
    #     search_results = soup.find_all("div", class_="g")
    #     for result in search_results:
    #         link = result.find("a")["href"]
    #         results.append(link)
    # if response.status_code == 429:
    #     raise ("429 Too Many Requests")
    for j in search(query, stop=num_results, pause=1.0):
        if "cnyes.com" in j:
            results.append(j.replace("print", "id"))
    return results


def Parameter_read(file):
    txtdata = txt_read(file).split("\n")
    try:
        sel = int(txtdata[0])
        level = int(txtdata[1])
        year = float(txtdata[2])
        e_eps = float(txtdata[3]) if txtdata[3].lower() != "none" else None
    except:
        sel, level, year, e_eps = default_Parameter
    return [sel, level, year, e_eps]


"""
parameter -> sel
Description: EPS year
# N: This year
# 0: N + 0
# 1: N + 1
# 2: N + 2

parameter -> level
Description: select forward eps value
# 0: high, 1: low, 2: average, 3: medium
"""


def ModifideParameter() -> list:
    msgList = [
        "EPS year:  (default is 1)\nN: This year\n\t0: N + 0\n\t1: N + 1\n\t2: N + 2",
        "select forward eps value:  (default is 3)\n\t0: high\n\t1: low\n\t2: average\n\t3: medium",
        "Reference how many years: (default is 4.5)",
        "e_eps (default is None):",
    ]
    float_input = [2, 3]

    Parameter = []
    with open("Parameter.txt", "w") as pf:
        for i in range(4):
            os.system("cls")
            print(msgList[i])
            UserInput = input("Input: ")
            try:
                if i in float_input:
                    Parameter.append(float(UserInput))
                else:
                    Parameter.append(int(UserInput))
            except:
                print(f"Use default Value: {default_Parameter[i]}")
                Parameter.append(default_Parameter[i])
                input()
            write2txt(Parameter[i], pf)

        print(f"your Parameter: {Parameter}")
        input()
    return Parameter

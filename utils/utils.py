import csv
import requests
from enum import Enum
from bs4 import BeautifulSoup
import plotly.graph_objects as go

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
}

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


def ResultOutput(title):
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
            "市場預估價",
            "市場預估價潛在漲幅"
        ]
    )
    return fw, csvwriter, csvfile

def get_google_search_results(query, num_results=10):
    results = []
    url = f"https://www.google.com/search?q={query}&num={num_results}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        search_results = soup.find_all("div", class_="g")
        for result in search_results:
            link = result.find("a")["href"]
            results.append(link)
    if response.status_code == 429:
        raise("429 Too Many Requests")
    return results
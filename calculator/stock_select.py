import requests
from bs4 import BeautifulSoup
from utils.utils import headers, isOrdinaryStock


def getETFConstituent(Database, etf: str) -> list[str]:
    url_template = "https://www.moneydj.com/ETF/X/Basic/Basic0007B.xdjhtm?etfid={}.TW"

    getList = []

    url = url_template.format(etf)

    result = requests.get(url, headers=headers)
    result.encoding = "utf-8"
    soup = BeautifulSoup(result.text, "html5lib")
    data = soup.find_all("td", class_="col05")
    for _, name in enumerate(data):
        getList.append(name.text)

    return Database.get_stockID(getList)


def getInstitutional_TOP50() -> list[str]:

    getList = []

    # 外資買賣超、投信買賣超、自營商買賣超
    buy_list = [
        "https://histock.tw/stock/three.aspx?s=a",
        "https://histock.tw/stock/three.aspx?s=b",
        "https://histock.tw/stock/three.aspx?s=c",
    ]

    for _, link in enumerate(buy_list):
        url = link
        result = requests.get(url, headers=headers)
        result.encoding = "utf-8"
        soup = BeautifulSoup(result.text, "html5lib")
        data = []

        data = soup.find_all("span", class_="w58")[::6]

        for _, name in enumerate(data):
            if isOrdinaryStock(name.text):
                getList.append(name.text)
    return list(set(getList))

import re
from natsort import natsorted
from utils.utils import fetch_webpage, isOrdinaryStock


def get_etf_constituents(etf_id: str) -> list[str]:
    """Get constituent stocks of an ETF"""
    url = f"https://www.moneydj.com/ETF/X/Basic/Basic0007B.xdjhtm?etfid={etf_id}.TW"
    soup = fetch_webpage(url)
    stock_id = [
        (re.search(r"etfid=(\d+)\.", a["href"]))[1] for a in soup.select("td.col05 a")
    ]

    return natsorted(stock_id)


def get_institutional_top50() -> list[str]:
    """Get top 50 stocks by institutional investors"""
    base_url = "https://histock.tw/stock/three.aspx?s={}"
    # a: foreign, b: investment trust, c: dealers
    investor_types = ["a", "b", "c"]

    all_stocks = []
    for investor_type in investor_types:
        soup = fetch_webpage(base_url.format(investor_type))
        stock_elements = soup.find_all("span", class_="w58")[::6]
        stocks = [name.text for name in stock_elements if isOrdinaryStock(name.text)]
        all_stocks.extend(stocks)

    return natsorted(list(set(all_stocks)))

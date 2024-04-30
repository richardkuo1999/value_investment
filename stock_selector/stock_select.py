import requests
from bs4 import BeautifulSoup
from utils.utils import headers
        
def getETFConstituent(all_stock_info, ETF_ID):
    url_template = "https://www.moneydj.com/ETF/X/Basic/Basic0007A.xdjhtm?etfid={}.TW"
    
    getList = []
    
    url = url_template.format(ETF_ID)

    result = requests.get(url, headers=headers)
    result.encoding = "utf-8"
    soup = BeautifulSoup(result.text, "html5lib")
    data = soup.find_all("td", class_="col05")
    for idx, name in enumerate(data):
        getList.append(name.text)
        
    stock_list = []
    for sn in getList:
        try:
            stock_id = all_stock_info.loc[all_stock_info["stock_name"] == sn].iloc[0][
                "stock_id"
            ]
            if stock_id[0] != '0':
                stock_list.append(stock_id)
        except:
            pass
    return stock_list
        
def getInstitutional_TOP50(all_stock_info):
    
    getList = []
    
    # 外資買賣超、投信買賣超、公股銀行買賣超
    buy_list = [
        "https://histock.tw/stock/three.aspx?s=b",
        "https://histock.tw/stock/three.aspx?s=c",
        "https://histock.tw/stock/broker8.aspx",
    ]
    

    for idx, link in enumerate(buy_list):
        url = link
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
            getList.append(txt)
        
        getList = list(set(getList))
        stock_list = []
        for sn in getList:
            try:
                stock_id = all_stock_info.loc[all_stock_info["stock_name"] == sn].iloc[0][
                    "stock_id"
                ]
                if stock_id[0] != '0':
                    stock_list.append(stock_id)
            except:
                pass
    return stock_list
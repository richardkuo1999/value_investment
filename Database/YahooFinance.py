from utils.utils import fetch_webpage


class YahooFinance:
    def __init__(self, stock_id, Market):
        self.stock_id = stock_id
        self.Market = Market
        self.summary = self.get_yahooFinanceDict()

    def get_yahooFinanceDict(self):
        yahooFinanceDict = {}
        url = f"https://finance.yahoo.com/quote/{self.stock_id}.{self.Market}/"
        soup = fetch_webpage(url)
        for item in soup.find("div", {"data-testid": "quote-statistics"}).select("li"):
            label = item.find("span", class_="label yf-dudngy").text
            value_span = item.find("span", class_="value yf-dudngy")
            fin_streamer = value_span.find("fin-streamer")

            if fin_streamer:
                value = fin_streamer["data-value"]
            else:
                value = value_span.text.strip()

            yahooFinanceDict[label] = value

        return yahooFinanceDict

    def get_1yTargetEst(self):
        data = None
        try:
            data = float(self.summary["1y Target Est"].replace(",", ""))
        except:
            pass
        return data

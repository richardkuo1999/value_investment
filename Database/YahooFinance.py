from utils.utils import fetch_webpage

# Get the Yahoo Finance summary for the stock
# This function is support Taiwan stock market only
class YahooFinance:
    def __init__(self, stock_id, Market):
        # Check if the Market is valid
        if Market != "TW" and Market != "TWO":
            print(f"Market: {Market} is not supported, please use TW or TWO")

        self.stock_id = stock_id
        self.Market = Market
        self.summary = self.get_yahooFinanceDict()
        
    def get_yahooFinanceDict(self):
        yahooFinanceDict = {}
        url = f"https://finance.yahoo.com/quote/{self.stock_id}.{self.Market}/"
        soup = fetch_webpage(url)
        
        # scrape the page for the desired data
        for item in soup.find("div", {"data-testid": "quote-statistics"}).select("li"):
            labels = item.find_all("span")
            if len(labels) < 2:
                continue

            # Get the key and value from the labels
            key = labels[0].text.strip()
            value = labels[1].text.strip()
            yahooFinanceDict[key] = value

        return yahooFinanceDict

    def get_1yTargetEst(self):
        data = None
        try:
            data = float(self.summary["1y Target Est"].replace(",", ""))
        except Exception as e:
            print(f"Error: {e}")
        return data

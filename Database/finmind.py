import requests
from FinMind.data import DataLoader


class Finminder:
    def __init__(self, allToken):
        self.TokenUSE = 0
        self.stock_id = None
        self.start_date = None
        self.TokenList = allToken["FinmindToken"]
        self.api = DataLoader()
        self.Login()
        self.taiwan_stock_info = self.get_taiwan_stock_info()

    def get_efficient_token(self) -> str:
        Token = self.TokenList[self.TokenUSE]

        resp = requests.get(
            "https://api.web.finmindtrade.com/v2/user_info",
            params={"token": Token},
        )
        api_request_limit = resp.json()["api_request_limit"]
        user_count = resp.json()["user_count"]
        print(
            f"{self.TokenUSE+1}: user_count/api_request_limit: {user_count}/{api_request_limit}"
        )
        if (api_request_limit - user_count) <= 50:
            self.TokenUSE = (self.TokenUSE + 1) % len(self.TokenList)
            return self.get_efficient_token()
        return Token

    def Login(self):
        return self.get_stock_data(
            "login_by_token", api_token=self.get_efficient_token()
        )

    def get_taiwan_stock_info(self):
        return self.get_stock_data("taiwan_stock_info")

    def get_stock_data(self, data_type: str, **kwargs):
        """Generic method to get stock data

        Args:
            data_type: Type of data to retrieve
            **kwargs: Additional arguments passed to API call
        """
        api_method = getattr(self.api, data_type)
        return api_method(**kwargs)

    def get_cnn_fear_greed_index(self, start_date):
        return self.get_stock_data("cnn_fear_greed_index", start_date=start_date)

    def get_taiwan_option_daily(self, option_id, start_date):
        return self.get_stock_data(
            "taiwan_option_daily", option_id=option_id, start_date=start_date
        )

    def get_taiex(self, start_date):
        return self.get_stock_data("tse", date=start_date)

    def get_stock_info(self, stock_id: str, tag1: str, tag2: str) -> str:
        """get the stock info according to tag2

        Args:
            stock_id (str): stock number
            tag1 (str): stock_id is stock number or stock name
            tag2 (str): stock_name or Listed Company/OTC

        Returns:
            str: according to yout tag2 what you want to get
        """
        return self.taiwan_stock_info.loc[
            self.taiwan_stock_info[tag1] == stock_id
        ].iloc[0][tag2]

    def get_stockID(self, getList: list[str]) -> list[str]:
        """Convert stock names to stock numbers

        Args:
            getList (list[str]): the stock number you want to get

        Returns:
            list[str]: stock number
        """
        stock_list = []
        for stock_name in getList:
            try:
                stock_id = self.get_stock_info(stock_name, "stock_name", "stock_id")
                if not stock_id.startswith("0"):
                    stock_list.append(stock_id)
            except:
                continue
        return stock_list

    def get_eps(self) -> list[float]:
        """Get EPS values

        Returns:
            List of EPS values
        """
        df = self.get_stock_data(
            "taiwan_stock_financial_statement",
            stock_id=self.stock_id,
            start_date=self.start_date,
        )
        return df[df.type == "EPS"]["value"].tolist()

    def get_closing_price(self) -> tuple[list[float]]:
        """Get closing prices

        Returns:
            tuple[list[float], list[float]]: data dates, closing price
        """
        stock_data = self.get_stock_data(
            "taiwan_stock_daily", stock_id=self.stock_id, start_date=self.start_date
        )
        return (stock_data["date"].tolist(), stock_data["close"].tolist())

    def get_per_pbr(self) -> tuple[list[float]]:
        """Get PER values

        Returns:
            tuple[list[float], list[float]]: data dates, PER
        """
        stock_data = self.get_stock_data(
            "taiwan_stock_per_pbr",
            stock_id=self.stock_id,
            start_date=self.start_date,
        )
        return {
            "date": stock_data["date"].tolist(),
            "PER": stock_data["PER"].tolist(),
            "PBR": stock_data["PBR"].tolist(),
        }

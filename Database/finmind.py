import time
import requests
from pathlib import Path
from FinMind.data import DataLoader


class Finminder:
    def __init__(self, Token):
        self.stock_number = None
        self.start_date = None
        self.Token = self.Load_token(Token)
        self.api = DataLoader()
        self.all_stock_info = self.Load_data()

    def Load_token(self, Token) -> str:
        return Token["FinmindToken"]

    def Load_data(self):
        self.api.login_by_token(api_token=self.Token)

        return self.api.taiwan_stock_info()

    def getCnnFearGreedIndex(self, start_date):
        return self.api.Cnn_Fear_Greed_Index(start_date)

    def get_stock_info(self, stock_id: str, tag1: str, tag2: str) -> str:
        """get the stock info according to tag2

        Args:
            stock_id (str): stock number
            tag1 (str): stock_id is stock number or stock name
            tag2 (str): stock_name or Listed Company/OTC

        Returns:
            str: according to yout tag2 what you want to get
        """
        all_stock_info = self.all_stock_info
        return all_stock_info.loc[all_stock_info[tag1] == stock_id].iloc[0][tag2]

    def get_stockID(self, getList: list[str]) -> list[str]:
        """stock name to stock number

        Args:
            getList (list[str]): the stock number you want to get

        Returns:
            list[str]: stock number
        """
        stock_list = []
        for stock_name in getList:
            try:
                stock_id = self.get_stock_info(stock_name, "stock_name", "stock_id")
                if stock_id[0] != "0":
                    stock_list.append(stock_id)
            except:
                pass
        return stock_list

    def Check_limit(self):
        """if api have times limit use this"""
        resp = requests.get(
            "https://api.web.finmindtrade.com/v2/user_info",
            params={"token": self.Token},
        )
        api_request_limit = resp.json()["api_request_limit"]
        user_count = resp.json()["user_count"]
        if (api_request_limit - user_count) <= 10:
            print(f"user_count/api_request_limit: {user_count}/{api_request_limit}")
            time.sleep(600)
            self.Check_limit()

    def get_EPS(self) -> list[float]:
        """get the EPS

        Returns:
            list[float]: eps
        """
        df = self.api.taiwan_stock_financial_statement(
            self.stock_number, self.start_date
        )
        lst_eps = df[df.type == "EPS"].values.tolist()
        lst_eps = [ll[3] for ll in lst_eps]
        return lst_eps

    def get_closing_price(self) -> tuple[list[float]]:
        """get the closing price

        Returns:
            tuple[list[float], list[float]]: data dates, closing price
        """
        stock_data = self.api.taiwan_stock_daily(self.stock_number, self.start_date)
        price = stock_data["close"].values.tolist()
        dates = stock_data["date"].values.tolist()
        return (dates, price)

    def get_PER(self) -> tuple[list[float]]:
        """Get the PER

        Returns:
            tuple[list[float], list[float]]: data dates, PER
        """
        stock_data = self.api.taiwan_stock_per_pbr(self.stock_number, self.start_date)
        per = stock_data["PER"].values.tolist()
        dates = stock_data["date"].values.tolist()
        return (dates, per)

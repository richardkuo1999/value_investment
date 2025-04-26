import os
import sys
import logging
import requests
from FinMind.data import DataLoader
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

sys.path.append(os.path.dirname(__file__) + "/..")
from utils.utils import load_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Finminder:
    def __init__(self, all_token):
        self.TokenUSE = 0
        self.stock_id = None
        self.start_date = None
        self.TokenList = all_token["FinmindToken"]
        self.api = DataLoader()
        self.login()
        self.taiwan_stock_info = self.get_taiwan_stock_info()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(10),
        retry=retry_if_exception_type((requests.RequestException, ValueError))
    )
    def get_efficient_token(self) -> str:
        url = "https://api.web.finmindtrade.com/v2/user_info"
        token = self.TokenList[self.TokenUSE]
        logger.info(f"Token {self.TokenUSE+1}")
        try:
            resp = requests.get(url, params={"token": token}, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            api_request_limit = data.get("api_request_limit", 0)
            user_count = data.get("user_count", 9999)
            logger.info("Token {}: user_count/api_request_limit: {}/{}"
                .format(self.TokenUSE+1, user_count, api_request_limit)
            )
            if api_request_limit - user_count <= 50:
                self.TokenUSE = (self.TokenUSE + 1) % len(self.TokenList)
                return self.get_efficient_token()
            return token
        except requests.RequestException as e:
            logger.error(f"Failed to check token {token}: {e}")
            self.TokenUSE = (self.TokenUSE + 1) % len(self.TokenList)
            raise

    def login(self) -> None:
        try:
            self.api.login_by_token(api_token=self.get_efficient_token())
            logger.info("Successfully logged in to FinMind API")
        except Exception as e:
            logger.error(f"Failed to login to FinMind API: {e}")
            raise

    def get_stock_data(self, data_type: str, **kwargs):
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_fixed(10),
            retry=retry_if_exception_type((requests.RequestException, ValueError))
        )
        def fetch_data():
            api_method = getattr(self.api, data_type)
            return api_method(**kwargs)

        try:
            result_data = fetch_data()
            logger.info(f"Successfully retrieved {data_type}")
            return result_data
        except Exception as e:
            logger.error(f"Failed to retrieve {data_type}: {e}")
            raise

    def get_taiwan_stock_info(self):
        return self.get_stock_data("taiwan_stock_info")

    def get_taiwan_option_daily(self, option_id: str, start_date: str):
        return self.get_stock_data(
            "taiwan_option_daily", option_id=option_id, start_date=start_date
        )

    def get_stock_info(self, stock_id: str, tag1: str, tag2: str) -> str:
        """get the stock info according to tag2

        Args:
            stock_id (str): stock number
            tag1 (str): stock_id is stock number or stock name
            tag2 (str): stock_name or Listed Company/OTC

        Returns:
            str: according to yout tag2 what you want to get
        """
        try:
            result = self.taiwan_stock_info[self.taiwan_stock_info[tag1] == stock_id]
            if result.empty:
                logger.warning(f"No stock info found for {tag1}={stock_id}")
                return None
            return result.iloc[0][tag2]
        except Exception as e:
            logger.error("Failed to retrieve stock info for {}={}, tag2={}: {}"
                         .format(tag1, stock_id, tag2, e))
            return None

    def get_stockID(self, getList: list[str]) -> list[str]:
        stock_list = []
        for stock_name in getList:
            try:
                stock_id = self.get_stock_info(stock_name, "stock_name", "stock_id")
                if stock_id and not stock_id.startswith("0"):  # Exclude OTC stocks
                    stock_list.append(stock_id)
                else:
                    logger.warning(f"Skipping invalid or OTC stock: {stock_name}")
            except Exception as e:
                logger.warning(f"Failed to convert stock name {stock_name} to ID: {e}")
                continue
        return stock_list

    def get_eps(self) -> list[float]:
        try:
            if not self.stock_id or not self.start_date:
                raise ValueError("stock_id and start_date must be set")
            df = self.get_stock_data(
                "taiwan_stock_financial_statement",
                stock_id=self.stock_id,
                start_date=self.start_date,
            )
            if df.empty or "type" not in df or "value" not in df:
                logger.warning(f"No EPS data found for stock {self.stock_id}")
                return []
            return df[df["type"] == "EPS"]["value"].astype(float).tolist()
        except Exception as e:
            logger.error(f"Failed to retrieve EPS for stock {self.stock_id}: {e}")
            return []

    def get_closing_price(self) -> tuple[list[float]]:
        try:
            if not self.stock_id or not self.start_date:
                raise ValueError("stock_id and start_date must be set")
            stock_data = self.get_stock_data(
                "taiwan_stock_daily", stock_id=self.stock_id, start_date=self.start_date
            )
            if stock_data.empty or "date" not in stock_data or "close" not in stock_data:
                logger.warning(f"No closing price data found for stock {self.stock_id}")
                return ([], [])
            return (stock_data["date"].tolist(), stock_data["close"].astype(float).tolist())
        except Exception as e:
            logger.error(f"Failed to retrieve closing prices for stock {self.stock_id}: {e}")
            return ([], [])

    def get_per_pbr(self) -> tuple[list[float]]:
        try:
            if not self.stock_id or not self.start_date:
                raise ValueError("stock_id and start_date must be set")
            stock_data = self.get_stock_data(
                "taiwan_stock_per_pbr",
                stock_id=self.stock_id,
                start_date=self.start_date,
            )
            if stock_data.empty or "PER" not in stock_data or "PBR" not in stock_data:
                logger.warning(f"No PER/PBR data found for stock {self.stock_id}")
                return ([], [])
            return (
                stock_data["PER"].astype(float).tolist(),
                stock_data["PBR"].astype(float).tolist()
            )
        except Exception as e:
            logger.error(f"Failed to retrieve PER/PBR for stock {self.stock_id}: {e}")
            return ([], [])

if __name__ == "__main__":
    # Example usage
    token = load_token()
    finminder = Finminder(token)
    finminder.stock_id = "2330"
    finminder.start_date = "2023-01-01"
    print(f"EPS: {finminder.get_eps()}")
    print(f"Closing Prices: {finminder.get_closing_price()}")
    print(f"PER/PBR: {finminder.get_per_pbr()}")
    print(f"Stock ID from Name: {finminder.get_stockID(['台積電'])}")
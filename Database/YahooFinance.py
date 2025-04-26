import os
import sys
import logging

sys.path.append(os.path.dirname(__file__) + "/..")
from utils.utils import fetch_webpage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class YahooFinance:
    SUPPORTED_MARKETS = ["TW", "TWO"]
    def __init__(self, stock_id: str, market: str):
        if market not in self.SUPPORTED_MARKETS:
            raise ValueError(f"Market '{market}' is not supported. Use 'TW' or 'TWO'.")

        self.stock_id = stock_id
        self.market = market
        self.summary = self._fetch_yahoo_finance_summary()
        
    def _fetch_yahoo_finance_summary(self) -> dict:
        url = f"https://finance.yahoo.com/quote/{self.stock_id}.{self.market}/"
        try:
            soup = fetch_webpage(url)
            summary_dict = {}

            # Locate the quote-statistics section
            stats_section = soup.find("div", {"data-testid": "quote-statistics"})
            if not stats_section:
                logger.warning("No quote statistics found for {}.{}"
                               .format(self.stock_id, self.market))
                return summary_dict

            # Parse each list item in the section
            for item in stats_section.select("li"):
                labels = item.find_all("span")
                if len(labels) < 2:
                    continue

                key = labels[0].text.strip()
                value = labels[1].text.strip()
                summary_dict[key] = value

            return summary_dict
        except Exception as e:
            logger.error("Failed to fetch Yahoo Finance data for {}.{}: {}"
                         .format(self.stock_id, self.market, e))
            return {}

    def get_1y_target_est(self) -> float | None:
        try:
            target_est = self.summary.get("1y Target Est", "").replace(",", "")
            return float(target_est) if target_est else None
        except (ValueError, TypeError) as e:
            logger.warning("Failed to parse 1y Target Est for {}.{}: {}"
                           .format(self.stock_id, self.market, e))
            return None

if __name__ == "__main__":
    stock_id = "2330"
    market = "TW"
    yahoo_finance = YahooFinance(stock_id, market)
    target_est = yahoo_finance.get_1y_target_est()
    print(f"1y Target Est for {stock_id}.{market}: {target_est}")
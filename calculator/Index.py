import os
import sys
import logging
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(__file__) + "/..")

from utils.output import telegram_print
from utils.utils import fetch_web2json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cnn_fear_greed_index() -> str:
    start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    base_url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    url = f"{base_url}/{start_date}"

    try:
        data = fetch_web2json(url).get('fear_and_greed', {})
        if not data:
            raise ValueError("未找到恐懼與貪婪指數數據")
        
        msgs = "\nCNN Fear and Greed Index:"
        msgs += f"\nDate: {data['timestamp']}"
        msgs += f"\nScore: {data['score']:.2f}"
        msgs += f"\nEmotion: {data['rating']}"
        return msgs
    except Exception as e:
        logger.error(f"獲取 CNN 恐懼與貪婪指數失敗: {e}")
        return "獲取 CNN 恐懼與貪婪指數失敗"

def get_latest_option_data(database, option_id, start_date):
    option_data = database.get_taiwan_option_daily(option_id, start_date)
    latest_date = option_data.iloc[-1]["date"]
    return option_data[option_data["date"] == latest_date]

def get_max_interest_price(option_data, contract_date, call_put):
    filtered_df = option_data[
        (option_data["contract_date"] == contract_date) \
                        & (option_data["call_put"] == call_put)
    ]
    interest_sum = filtered_df.groupby(["strike_price"])["open_interest"].sum()
    return interest_sum.idxmax(), interest_sum.max()

def format_contract_info(contract_date, put_price, put_val, call_price, call_val) -> str:
    return (
        f"到期月份:{contract_date:<10}\n"
        f"支撐: {put_price:.0f}/{put_val:<5}價/口\n"
        f"壓力: {call_price:.0f}/{call_val:<5}價/口\n\n"
    )
    
def option_support_and_pressure(database) -> str:
    start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    option_id = "TXO"
    
    try:
        option_data = get_latest_option_data(database, option_id, start_date)
        contract_dates = option_data["contract_date"].unique().tolist()
        
        msgs = "\n台指期選擇權支撐、壓力\n\n"
        for contract_date in contract_dates:
            call_price, call_val = get_max_interest_price(option_data, contract_date, "call")
            put_price, put_val = get_max_interest_price(option_data, contract_date, "put")
            msgs += format_contract_info(contract_date, put_price, put_val, call_price, call_val)
        return msgs
    except Exception as e:
        logger.error(f"生成期權支撐與壓力失敗: {e}")
        return "生成期權支撐與壓力失敗"

def notify_macro_indicators(finmind_db):
    telegram_print(cnn_fear_greed_index())
    telegram_print(option_support_and_pressure(finmind_db))

if __name__ == "__main__":
    from Database.Finmind import Finminder
    from utils.utils import load_token

    token = load_token()
    finmind_db = Finminder(token)
    notify_macro_indicators(finmind_db)
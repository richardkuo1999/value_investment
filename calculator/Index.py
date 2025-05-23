import os
import sys
import asyncio
import aiohttp
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(__file__) + "/..")

from Database.Finmind import Finminder
from utils.output import telegram_print
from utils.utils import logger, fetch_web2json


CNN_FEAR_GRED_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{}"

async def cnn_fear_greed_index(session) -> str:
    start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    url = CNN_FEAR_GRED_URL.format(start_date)

    try:
        data = (await fetch_web2json(session, url)).get("fear_and_greed")
        if not data:
            raise ValueError("未找到恐懼與貪婪指數數據")

        return (
            "\nCNN Fear and Greed Index:\n"
            f"Date: {data['timestamp']}\n"
            f"Score: {data['score']:.2f}\n"
            f"Emotion: {data['rating']}"
        )
    except Exception as e:
        logger.error(f"獲取 CNN 恐懼與貪婪指數失敗: {e}")
        return "獲取 CNN 恐懼與貪婪指數失敗"


async def option_support_and_pressure(database, session) -> str:
    start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    option_id = "TXO"

    async def __get_latest_option_data(database, session, option_id, start_date):
        option_data = await database.get_taiwan_option_daily(session, option_id, start_date)
        latest_date = option_data.iloc[-1]["date"]
        return option_data[option_data["date"] == latest_date]

    def __get_max_interest_price(option_data, contract_date, call_put):
        try:
            filtered_df = option_data[
                (option_data["contract_date"] == contract_date)
                & (option_data["call_put"] == call_put)
            ]
            if filtered_df.empty:
                raise ValueError(f"無符合條件的數據: {contract_date}, {call_put}")
            interest_sum = filtered_df.groupby("strike_price")["open_interest"].sum()
            if interest_sum.empty:
                raise ValueError("未找到未平倉量數據")
            return interest_sum.idxmax(), interest_sum.max()
        except Exception as e:
            logger.error(f"計算最大未平倉量失敗: {e}")
            return 0, 0

    def __format_contract_info(
        contract_date, put_price, put_val, call_price, call_val
    ) -> str:
        return (
            f"到期月份:{contract_date:<10}\n"
            f"支撐: {put_price:.0f}/{put_val:<5}價/口\n"
            f"壓力: {call_price:.0f}/{call_val:<5}價/口\n\n"
        )

    try:
        option_data = await __get_latest_option_data(database, session, option_id, start_date)
        if option_data is None:
            raise ValueError("無法獲取期權數據")
        contract_dates = option_data["contract_date"].unique().tolist()
        if not contract_dates:
            raise ValueError("無有效的合約日期")
        msgs = "\n台指期選擇權支撐、壓力\n\n"
        for contract_date in contract_dates:
            call_price, call_val = __get_max_interest_price(
                option_data, contract_date, "call"
            )
            put_price, put_val = __get_max_interest_price(
                option_data, contract_date, "put"
            )
            msgs += __format_contract_info(
                contract_date, put_price, put_val, call_price, call_val
            )
        return msgs
    except Exception as e:
        logger.error(f"生成期權支撐與壓力失敗: {e}")
        return "生成期權支撐與壓力失敗"


async def notify_macro_indicators(tokens, session):
    finmind_db = Finminder(tokens)
    try:
        tasks = [
            cnn_fear_greed_index(session),
            option_support_and_pressure(finmind_db, session)
        ]
        cnn_result, option_result = await asyncio.gather(*tasks, return_exceptions=True)
        telegram_print(cnn_result)
        telegram_print(option_result)
    except Exception as e:
        logger.error(f"通知宏觀指標失敗: {e}")

async def main():
    tokens = load_token()
    async with aiohttp.ClientSession() as session:
        await notify_macro_indicators(tokens, session)

if __name__ == "__main__":
    from Database.Finmind import Finminder
    from utils.utils import load_token
    asyncio.run(main())
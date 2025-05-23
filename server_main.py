import os
import sys
import logging
import aiohttp
import asyncio
import threading
from pathlib import Path


sys.path.append(os.path.dirname(__file__))

from utils.output import result_output, telegram_print
from calculator.calculator import calculator
from calculator.Index import notify_macro_indicators
from calculator.stock_select import fetch_etf_constituents, fetch_institutional_top50
from utils.utils import logger, load_token, get_profit, get_target, load_data


daily_run_lock = threading.Lock()

level = 4       # EPS level: 1-high, 2-low, 3-average, 4-medium
year = 4.5      # Calculation period (years)

USER_CHOICE = [
    "1560", "2337", "2351", "2455", "2458", "2467", "2645", "3004", "3006",
    "3081", "3455","3563", "3587", "3596", "3708", "4906", "5306", "5388",
    "6271", "6438", "6679", "6768", "6937", "6957", "8027", "8210", "8936",
    "9914", "9938", "2247", "3479", "6906"
]

async def get_catch():
    last_path = Path("results", "new")
    backup_path = Path("results", "backup")

    last_path.mkdir(parents=True, exist_ok=True)
    backup_path.mkdir(parents=True, exist_ok=True)

    catchs = {}
    tasks = [
        load_data(backup_path),
        load_data(last_path)
    ]
    backup, last = await asyncio.gather(*tasks, return_exceptions=True)
    catchs.update(backup)
    catchs.update(last)
    return catchs

async def individual_search(stocklist, EPS_lists, params):
    result_path = Path("results", "Individual",)
    result_path.mkdir(parents=True, exist_ok=True)
    tokens = load_token()
    params = [params[0] or level, params[1] or year]
    catchs = await get_catch()

    for file in result_path.rglob("*"):
        if file.is_file() and file.stem == "Individual":
            file.unlink()

    async with aiohttp.ClientSession() as session:
        stock_datas = await calculator(session, stocklist, params, tokens, catchs)
    stock_texts = result_output(result_path / Path("Individual"), stock_datas, EPS_lists)

    logging.shutdown()

    return stock_datas, stock_texts

async def get_institutional_data(session, result_path: Path, params: list, catch=None) -> dict:
    tokens = load_token()

    last_data = await load_data(result_path)

    stock_list = await fetch_institutional_top50(session)
    existing_data = {sid: last_data[sid] for sid in stock_list if sid in last_data}
    missing_ids = [sid for sid in stock_list if sid not in last_data]

    resultdata = await calculator(session, missing_ids, params, tokens, catch)

    resultdata.update(existing_data)
    return resultdata

class UnderEST:
    @staticmethod
    async def get_underestimated(result_path: Path) -> dict:
        last_data = await load_data(result_path)
        unders_est_data = {stock_id: data \
                            for stock_id, data in last_data.items()
                            if UnderEST.is_underestimated(data)
                        }
        return unders_est_data

    @staticmethod
    def notify_unders_est(underestimated_dict: dict) -> str:
        msg = "Under Stimated\n"
        unsorted_list = []
        for stock_id, data in underestimated_dict.items():
            name = data.get("名稱")
            business = data.get('產業')
            profit = UnderEST.get_expected_profit(data)
            unsorted_list.append([stock_id, name, business, profit])
        sorted_list = sorted(unsorted_list, key=lambda x: x[3], reverse=True)
        for stock_id, name, business, profit in sorted_list:
            stock_id = str(stock_id).split('.')[0]
            msg += f"{stock_id:<5} {name:<6} {business:<6} {profit:>5.1f}%\n"
        telegram_print(msg)
        return msg

    @staticmethod
    def is_underestimated(StockData):
        return UnderEST.get_expected_profit(StockData) > 0.0

    @staticmethod
    def get_expected_profit(data: dict) -> float:
        eps = data.get("EPS(EST)") or data.get("EPS(TTM)")
        price = data.get("價格")
        target = get_target(data.get("PE(TL-1SD)"), eps)
        
        return get_profit(target, price) if(eps > 0) else -1
    
async def main_run(run_lists, DAILY_RUN_LISTS):
    result_path = Path("results", "new")
    backup_path = Path("results", "backup")
    tokens = load_token()
    params = [level, year]

    catchs = await get_catch()

    stock_groups = {}

    for file in result_path.rglob("*"):
        if file.is_file() and (file.stem in run_lists or file.stem == "Understimated"):
            file.replace(backup_path / file.name)

    stock_groups = {}
    async with aiohttp.ClientSession() as session:
        for etf in DAILY_RUN_LISTS:
            if etf in run_lists:
                stock_groups[etf] = USER_CHOICE if etf == "User_Choice" else await fetch_etf_constituents(session, etf)

        # TODO 評估要不要異步化
        for title, stocklist in stock_groups.items():
            telegram_print(f"Start Run\n{title}")
            resultdata = await calculator(session, stocklist, params, tokens, catchs)
            result_output(result_path / Path(title), resultdata)

        # Wait all async finished
        await asyncio.sleep(5)

        unders_est_data = {}
        try:
            unders_est_data = await UnderEST.get_underestimated(result_path)
            result_output(result_path / Path("Understimated"), unders_est_data)
        except Exception as e:
            logger.error(f"Error in getting underestimated stocks: {e}")
        try:
            UnderEST.notify_unders_est(unders_est_data)
        except Exception as e:
            logger.error(f"Error in Notify underestimated stocks: {e}")
            logger.error(f"unders_est_data: {unders_est_data}")

        if "Institutional_TOP50" in run_lists:
            try:
                telegram_print("Start Run\nInstitutional_TOP50")
                resultdata = await get_institutional_data(session, result_path, params, catchs)
                result_output(result_path / Path("Institutional_TOP50"), resultdata)
            except Exception as e:
                logger.error(f"Error in getting institutional data: {e}")

        try:
            await notify_macro_indicators(tokens, session)
        except Exception as e:
            logger.error(f"Error in notifying macro indicators: {e}")

async def daily_run(DAILY_RUN_LISTS, IP_ADDR):
    if daily_run_lock.acquire(blocking=False):
        telegram_print("Start Daily Run")
        try:
            await main_run(DAILY_RUN_LISTS, DAILY_RUN_LISTS)
            telegram_print("Daily Run Finished")
        except Exception as e:
            logger.error(f"Daily run error: {e}")
            telegram_print(f"Daily run error: {e}")
        finally:
            telegram_print(
                f"Download link:\nCSV: http://{IP_ADDR}:8000/download/csv\n" \
                f"TXT: http://{IP_ADDR}:8000/download/txt"
            )
            daily_run_lock.release()
            logging.shutdown()

async def force_run(run_lists, DAILY_RUN_LISTS, IP_ADDR):
    if daily_run_lock.acquire(blocking=False):
        try:
            await main_run(run_lists, DAILY_RUN_LISTS)
        except Exception as e:
            logger.error(f"Force run error: {e}")
            telegram_print(f"Force run error: {e}")
        finally:
            telegram_print(
                f"Download link:\nCSV: http://{IP_ADDR}:8000/download/csv\n" \
                f"TXT: http://{IP_ADDR}:8000/download/txt"
            )
            daily_run_lock.release()
            logging.shutdown()

async def main():
        result_path = Path("results", "new")
        unders_est_data = await UnderEST.get_underestimated(result_path)
        result = result_output(result_path / Path("Understimated"), unders_est_data)
        UnderEST.notify_unders_est(unders_est_data)

if __name__ == "__main__":
    asyncio.run(main())
import os
import sys
import threading
from pathlib import Path
import logging


sys.path.append(os.path.dirname(__file__))

from utils.output import result_output, telegram_print
from Database.Finmind import Finminder
from calculator.calculator import calculator
from calculator.Index import notify_macro_indicators
from calculator.stock_select import fetch_etf_constituents, fetch_institutional_top50
from utils.utils import load_token, get_profit, get_target, get_last_data

logger = logging.getLogger(__name__)

daily_run_lock = threading.Lock()

level = 4       # EPS level: 1-high, 2-low, 3-average, 4-medium
year = 4.5      # Calculation period (years)

USER_CHOICE = [
    "1560", "2337", "2351", "2455", "2458", "2467", "3006", "3081", "3455",
    "3563", "3587", "3596", "3708", "4768", "4906", "5236", "5306", "5388",
    "5469", "6271", "6438", "6664", "6937", "6957", "8027", "8358", "8936", "9914",
]

def get_catch():
    result_path = Path("results", "new")
    backup_path = Path("results", "backup")

    result_path.mkdir(parents=True, exist_ok=True)
    backup_path.mkdir(parents=True, exist_ok=True)

    catch = {}
    catch.update(get_last_data(backup_path))
    catch.update(get_last_data(result_path))
    return catch

def individual_search(stock_lists, EPS_lists, params):
    result_path = Path("results", "Individual",)
    result_path.mkdir(parents=True, exist_ok=True)
    for file in result_path.rglob("*"):
        if file.is_file() and file.stem == "Individual":
            file.unlink()

    token = load_token()
    db = Finminder(token)
    params = [params[0] or level, params[1] or year]

    stock_datas = calculator(db, stock_lists, params, get_catch())
    stock_texts = result_output(result_path / Path("Individual"), stock_datas, EPS_lists)

    return stock_datas, stock_texts

def get_institutional_data(db, result_path: Path, params: list, catch=None) -> dict:

    stock_list = fetch_institutional_top50()
    last_data = get_last_data(result_path)

    existing_data = {sid: last_data[sid] for sid in stock_list if sid in last_data}
    missing_ids = [sid for sid in stock_list if sid not in last_data]

    resultdata = calculator(db, missing_ids, params, catch)
    resultdata.update(existing_data)
    return resultdata

class UnderEST:
    @staticmethod
    def get_underestimated(result_path: Path) -> dict:
        last_data = get_last_data(result_path)
        unders_est_data = {stock_id: data \
                            for stock_id, data in last_data.items()
                            if UnderEST.is_underestimated(data)
                        }
        return unders_est_data

    @staticmethod
    def notify_unders_est(underestimated_dict: dict) -> str:
        msg = "Under Stimated\n"
        for stock_id, data in underestimated_dict.items():
            name = data.get("名稱", "")
            profit = UnderEST.get_expected_profit(data)
            msg += f"{stock_id}{name}: {profit:.1f}%\n"

        telegram_print(msg)
        return msg

    @staticmethod
    def is_underestimated(StockData):
        return UnderEST.get_expected_profit(StockData) > 0.0

    @staticmethod
    def get_expected_profit(data: dict) -> float:
        eps = data.get("EPS(EST)") or data.get("EPS(TTM)", 0)
        price = data.get("價格", 0)
        target = get_target(data.get("PE(TL-1SD)", 0.0), eps)
        return get_profit(target, price)
    
def main_run(run_lists, DAILY_RUN_LISTS):
    result_path = Path("results", "new")
    backup_path = Path("results", "backup")

    catch = get_catch()

    stock_groups = {}
   
    for file in result_path.rglob("*"):
        if file.is_file() and file.stem in run_lists:
            file.rename(backup_path / file.name)

    stock_groups = {}
    for etf in DAILY_RUN_LISTS:
        if etf in run_lists:
            stock_groups[etf] = USER_CHOICE if etf == "User_Choice" else fetch_etf_constituents(etf)

    params = [level, year]

    token = load_token()
    db = Finminder(token)

    for title, stocklist in stock_groups.items():
        telegram_print(f"Start Run\n{title}")
        resultdata = calculator(db, stocklist, params, catch)
        result_output(result_path / Path(title), resultdata)


    try:
        for file in result_path.rglob("*"):
            if file.is_file() and file.stem == "Understimated":
                file.rename(backup_path / file.name)
        unders_est_data = UnderEST.get_underestimated(result_path)
        result_output(result_path / Path("Understimated"), unders_est_data)
    except Exception as e:
        logger.error(f"Error in getting underestimated stocks: {e}")

    try:
        telegram_print("Start Run\nInstitutional_TOP50")
        for file in result_path.rglob("*"):
            if file.is_file() and file.stem == "nInstitutional_TOP50":
                file.rename(backup_path / file.name)
        resultdata = get_institutional_data(db, result_path, params, catch)
        result_output(result_path / Path("Institutional_TOP50"), resultdata)
    except Exception as e:
        logger.error(f"Error in getting institutional data: {e}")
    

        UnderEST.notify_unders_est(unders_est_data)
    try:
        notify_macro_indicators(db)
    except Exception as e:
        logger.error(f"Error in notifying macro indicators: {e}")

def daily_run(DAILY_RUN_LISTS, IP_ADDR):
    if daily_run_lock.acquire(blocking=False):
        telegram_print("Start Daily Run")
        try:
            main_run(DAILY_RUN_LISTS, DAILY_RUN_LISTS)
            telegram_print("Daily Run Finished")
        except Exception as e:
            logger.error(f"Daily run error: {e}")
            telegram_print(f"Daily run error: {e}")
        finally:
            daily_run_lock.release()
            telegram_print(
                f"Download link:\nCSV: http://{IP_ADDR}:8000/download/csv\n" \
                f"TXT: http://{IP_ADDR}:8000/download/txt"
            )

def force_run(run_lists, DAILY_RUN_LISTS, IP_ADDR):
    if daily_run_lock.acquire(blocking=False):
        try:
            main_run(run_lists, DAILY_RUN_LISTS)
        except Exception as e:
            logger.error(f"Force run error: {e}")
            telegram_print(f"Force run error: {e}")
        finally:
            daily_run_lock.release()
            telegram_print(
                f"Download link:\nCSV: http://{IP_ADDR}:8000/download/csv\n" \
                f"TXT: http://{IP_ADDR}:8000/download/txt"
            )

if __name__ == "__main__":
    pass
    # run_daily_task()
    # thread1 = threading.Thread(target=print_numbers, args=("Thread-1", 1))  # 每秒打印一次數字
    # thread2 = threading.Thread(target=print_numbers, args=("Thread-2", 2))  # 每兩秒打印一次數字

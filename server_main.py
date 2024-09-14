import pytz
import time
import yaml
import threading
from pathlib import Path
from Database.finmind import Finminder
from datetime import datetime, timedelta

from utils.utils import Parameter_read, Line_print, upload_files
from calculator.calculator import calculator
from calculator.stock_select import getETFConstituent

ETFList = ["0050", "006201", "0051"]
# ETFList = []
User_Choice = ["8069", "2345", "2330", "3661", "2454", "6679", "3035"]
# User_Choice = ["8069"]


def run():
    # Line_print("Daily Run Start")
    old_result = Path("results", "last_result")
    new_result = Path("results", "new_result")
    TokenPath = Path("token.yaml")
    ParameterPath = Path("Parameter.txt")

    with open(TokenPath, "r") as file:
        Token = yaml.safe_load(file)

    # create folder
    new_result.mkdir(parents=True, exist_ok=True)
    old_result.mkdir(parents=True, exist_ok=True)
    if new_result.exists():
        for file in new_result.iterdir():
            file.rename((old_result / file.name))

    upload_files(Path("results/last_result"), Token, "gdToken.json")

    # Read the caculate Parameter
    if ParameterPath.exists():
        parameter = Parameter_read(ParameterPath)

    Database = Finminder(Token)

    StockLists = {"User_Choice": User_Choice}

    for etf in ETFList:
        StockLists[etf] = getETFConstituent(Database, etf)

    for title, StockList in StockLists.items():
        Line_print(f"Start Run\n{title}\n{StockList}")

        # Get Data
        calculator(Database, StockList, parameter, new_result / Path(title))

        upload_files(Path("results/new_result"), Token, "gdToken.json")
        Line_print(f"{title} Finish\
                   \nDownload from: https://drive.google.com/drive/u/0/folders/{Token["result_path"]}"
                   )
    Line_print("Daily Run Finished")


def daily_run():
    taiwan_tz = pytz.timezone("Asia/Taipei")
    while True:
        taiwan_time = datetime.now(taiwan_tz)
        today_8pm = taiwan_time.replace(hour=20, minute=0, second=0, microsecond=0)

        next_time_run = today_8pm
        if taiwan_time >= today_8pm:
            next_time_run = next_time_run + timedelta(days=1)

        remaining_time = next_time_run - taiwan_time

        Line_print(f"Next run : {next_time_run}")
        time.sleep(remaining_time.total_seconds())
        run()


if __name__ == "__main__":
    run()
    daily_run()

    # thread1 = threading.Thread(target=print_numbers, args=("Thread-1", 1))  # 每秒打印一次數字
    # thread2 = threading.Thread(target=print_numbers, args=("Thread-2", 2))  # 每兩秒打印一次數字

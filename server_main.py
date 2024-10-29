import os
import sys
import pytz
import time
import yaml
import threading
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__)))

from Database.finmind import Finminder
from utils.utils import (
    Parameter_read,
    Line_print,
    UnderEST,
    upload_files,
)
from calculator.calculator import calculator
from calculator.stock_select import getETFConstituent

ETFList = ["0050", "006201", "0051"]
# ETFList = []
User_Choice = [
    "3708",
    "1560",
    "5388",
    "2455",
    "5236",
    "6271",
    "8936",
    "3167",
    "6937",
    "4739",
    "2467",
    "4768",
    "3042",
    "3006",
    "3596",
    "5306",
    "4906",
    "5469",
    "3563",
    "3455",
    "4721",
    "6664",
    "3081",
    "3583",
    "6438",
    "8358",
    "8027",
    "3587",
    "2351",
]
# User_Choice = ["8069"]


def Individual_search(StockLists, EPSLists):

    new_result = Path("results", "Individual")
    TokenPath = Path("token.yaml")
    ParameterPath = Path("Parameter.txt")

    # create folder
    new_result.mkdir(parents=True, exist_ok=True)
    for file in new_result.rglob("*"):
        if file.is_file():
            file.unlink()

    # Read the caculate Parameter
    if ParameterPath.exists():
        parameter = Parameter_read(ParameterPath)

    with open(TokenPath, "r") as file:
        Token = yaml.safe_load(file)

    Database = Finminder(Token)

    # Get Data
    StockData = calculator(
        Database, StockLists, EPSLists, parameter, new_result / Path("Individual")
    )

    return StockData


def run():
    TokenPath = Path("token.yaml")
    ParameterPath = Path("Parameter.txt")
    new_result = Path("results")

    # create folder
    new_result.mkdir(parents=True, exist_ok=True)
    for file in new_result.rglob("*"):
        if file.is_file():
            file.unlink()

    # Read the caculate Parameter
    if ParameterPath.exists():
        parameter = Parameter_read(ParameterPath)

    with open(TokenPath, "r") as file:
        Token = yaml.safe_load(file)
    Database = Finminder(Token)

    StockLists = {"User_Choice": User_Choice}

    for etf in ETFList:
        StockLists[etf] = getETFConstituent(Database, etf)

    EPSLists = []
    UndersESTList = []

    for title, StockList in StockLists.items():
        Line_print(f"Start Run\n{title}\n{StockList}")
        # Get Data
        StockDatas = calculator(
            Database, StockList, EPSLists, parameter, new_result / Path(title)
        )

        UndersESTList.extend(UnderEST.getUnderstimated(StockDatas))
    UnderEST.saveUnderstimated(UndersESTList, new_result / Path("Understimated"))

    # upload_files(Path("results"), Token, "gdToken.json")
    Line_print("Daily Run Finished")
    UnderEST.NoticeUndersEST(UndersESTList)
    # Line_print(f"Download from: https://drive.google.com/drive/u/0/folders/{Token["new_result"]}"
    #             )


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
        Line_print(f"Start Daily Run")
        run()


if __name__ == "__main__":
    daily_run()

    # thread1 = threading.Thread(target=print_numbers, args=("Thread-1", 1))  # 每秒打印一次數字
    # thread2 = threading.Thread(target=print_numbers, args=("Thread-2", 2))  # 每兩秒打印一次數字

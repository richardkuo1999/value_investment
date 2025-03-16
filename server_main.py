import os
import sys
import pytz
import time
import yaml
import threading
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__)))

from utils.output import ResultOutput
from Database.finmind import Finminder
from utils.Parameter import Parameter_read
from calculator.calculator import calculator
from calculator.Index import NotifyMacroeconomics
from utils.utils import Telegram_print, UnderEST, getLasturl
from calculator.stock_select import get_etf_constituents, get_institutional_top50

ETFList = ["0050", "006201", "0051"]
# ETFList = []
User_Choice = [
    "1560",
    "2337",
    "2351",
    "2455",
    "2458",
    "2467",
    "3006",
    "3042",
    "3081",
    "3455",
    "3563",
    "3587",
    "3596",
    "3708",
    "4768",
    "4906",
    "5236",
    "5306",
    "5388",
    "5469",
    "6271",
    "6438",
    "6664",
    "6937",
    "6957",
    "8027",
    "8358",
    "8936",
    "9914",
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
    StockDatas = calculator(Database, StockLists, parameter)
    ResultOutput(new_result / Path("Individual"), StockDatas, EPSLists)

    return StockDatas


def getInstitutional(Database, StockDatas_dict, parameter, CatchURL):
    EPSLists = None

    StockList = get_institutional_top50()
    Telegram_print(f"Start Run\nInstitutional_TOP50")

    isGetList = StockDatas_dict.keys()
    temp = {}
    notGetList = []
    for stockID in StockList:
        if stockID in isGetList:
            temp.update({stockID: StockDatas_dict[stockID]})
        else:
            notGetList.append(stockID)
    # Get Data
    StockDatas = calculator(Database, notGetList, parameter, CatchURL)
    StockDatas.update(temp)

    return StockDatas


def run():
    TokenPath = Path("token.yaml")
    ParameterPath = Path("Parameter.txt")
    new_result = Path("results")
    backup = Path("backup")
    CatchURL = {}
    # create folder
    new_result.mkdir(parents=True, exist_ok=True)
    backup.mkdir(parents=True, exist_ok=True)
    for file in backup.rglob("*"):
        if file.is_file():
            file.unlink()

    for file in new_result.rglob("*"):
        if file.is_file():
            CatchURL.update(getLasturl(file))
            file.rename(backup / file.name)

    # Read the caculate Parameter
    if ParameterPath.exists():
        parameter = Parameter_read(ParameterPath)

    with open(TokenPath, "r") as file:
        Token = yaml.safe_load(file)
    Database = Finminder(Token)

    StockLists = {"User_Choice": User_Choice}

    for etf in ETFList:
        StockLists[etf] = get_etf_constituents(etf)

    EPSLists = None
    StockDatas_dict = {}

    for title, StockList in StockLists.items():
        Telegram_print(f"Start Run\n{title}")
        # Get Data
        StockDatas = calculator(
            Database,
            StockList,
            parameter,
            CatchURL,
        )
        ResultOutput(new_result / Path(title), StockDatas)
        StockDatas_dict.update(StockDatas)

    # get Understimated
    UndersESTDict = UnderEST.getUnderstimated(StockDatas_dict)
    ResultOutput(new_result / Path("Understimated"), UndersESTDict, EPSLists)

    # get Institutional
    InstitutionalDatas = getInstitutional(
        Database, StockDatas_dict, parameter, CatchURL
    )
    ResultOutput(new_result / Path("Institutional_TOP50"), InstitutionalDatas, EPSLists)

    Telegram_print("Daily Run Finished")
    UnderEST.NotifyUndersEST(UndersESTDict)
    NotifyMacroeconomics(Database)
    Telegram_print(
        "Down load link:\nCSV: http://54.205.241.96:8000/download/csv\nTXT: http://54.205.241.96:8000/download/txt"
    )


def daily_run():
    taiwan_tz = pytz.timezone("Asia/Taipei")

    while True:
        taiwan_time = datetime.now(taiwan_tz)
        today_8pm = taiwan_time.replace(hour=20, minute=0, second=0, microsecond=0)

        next_time_run = today_8pm
        if taiwan_time >= today_8pm:
            next_time_run = next_time_run + timedelta(days=1)

        remaining_time = next_time_run - taiwan_time

        Telegram_print(f"Next run : {next_time_run}")
        time.sleep(remaining_time.total_seconds())
        Telegram_print(f"Start Daily Run")
        run()


if __name__ == "__main__":
    pass
    # daily_run()
    # thread1 = threading.Thread(target=print_numbers, args=("Thread-1", 1))  # 每秒打印一次數字
    # thread2 = threading.Thread(target=print_numbers, args=("Thread-2", 2))  # 每兩秒打印一次數字

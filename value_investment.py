import shutil
from termcolor import *
import os
from pathlib import Path


from calculator.stock_select import getETFConstituent, getInstitutional_TOP50
from calculator.calculator import calculator
from utils.utils import ResultOutput, ModifideParameter, Parameter_read
from Database.finmind import Finminder


"""
parameter -> sel
Description: EPS year
# N: This year
# 0: N + 0
# 1: N + 1
# 2: N + 2

parameter -> level
Description: select forward eps value
# 0: high, 1: low, 2: average, 3: medium
"""


if __name__ == "__main__":
    old_result = Path("results", "last_result")
    new_result = Path("results", "new_result")
    TokenPath = Path("token.txt")
    ParameterPath = Path("Parameter.txt")

    Database = Finminder(TokenPath)

    # create folder
    if not new_result.exists():
        new_result.mkdir(parents=True, exist_ok=True)
    else:
        old_result.mkdir(parents=True, exist_ok=True)
        os.system("ls")
        os.system("ls results")
        for file in new_result.iterdir():
            file.rename((old_result / file.name))

    # Read the caculate Parameter
    if ParameterPath.exists():
        parameter = Parameter_read(ParameterPath)
    else:
        parameter = ModifideParameter()

    while True:
        os.system("cls")
        UserInput = input(
            "1. 查詢ETF成分股 \n2. 查詢個股 \n3. 三大法人買賣超 \n4. 參數更改 \n5. 退出 \n輸入: "
        )
        StockLists = {}

        # 1. 查詢ETF成分股
        if UserInput == "1":
            UserInput = input("1.0050, 006201, 0051\n2. 自行輸入\n輸入: ")
            ETFList = []
            if UserInput == "1":
                ETFList = ["0050", "006201", "0051"]
            elif UserInput == "2":
                ETFList = input("請用空格隔開: ").split(" ")
            for etf in ETFList:
                StockLists[etf] = getETFConstituent(Database, etf)

        # 2. 查詢個股
        elif UserInput == "2":
            StockLists = {"User_Choice": input("請用空格隔開: ").split(" ")}

        # 3.三大法人買賣超
        elif UserInput == "3":
            StockLists = {" Institutional_Investors": getInstitutional_TOP50(Database)}

        # 4. 參數更改
        elif UserInput == "4":
            parameter = ModifideParameter()

        # 5. 退出
        elif UserInput == "5":
            break

        else:
            print("Enter Error!!")
            input()
            continue

        for title, StockList in StockLists.items():
            print(title, StockList)
            fw, cw, csvfile = ResultOutput(new_result, title)

            # Get Data
            calculator(
                Database,
                StockList,
                parameter,
                fw,
                cw,
            )

            fw.close()
            csvfile[0].close()
            csvfile[1].close()
        print("Enter to continue...")
        input()

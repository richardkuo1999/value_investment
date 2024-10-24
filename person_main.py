import os
import sys
import yaml
import shutil
from termcolor import *
from pathlib import Path
from Database.finmind import Finminder
import argparse

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

parser = argparse.ArgumentParser()
parser.add_argument("-sel",   type=int, default=1, help='Select EPS year, N: This year, 0: N+0, 1: N+1, 2: N+2')
parser.add_argument("-level", type=int, default=4, help='Select forward eps value\n1: high, 2: low, 3: average, 4: medium')
parser.add_argument("-year",  type=float, default=4.5, help="Data calculation length(unit:year)")
parser.add_argument("-e_eps", type=float, default=None)

args = parser.parse_args()

sys.path.append(os.path.join(os.path.dirname(__file__)))

from calculator.stock_select import getETFConstituent, getInstitutional_TOP50
from calculator.calculator import calculator
from utils.utils import ModifideParameter, Parameter_read



if __name__ == "__main__":
    new_result = Path("results")
    EPSLists = [] # set your EST eps in here
    with open("token.yaml", "r") as file:
        Token = yaml.safe_load(file)

    Database = Finminder(Token)

    # create folder
    new_result.mkdir(parents=True, exist_ok=True)

    # Read the caculate Parameter
    parameter = [args.level, args.year, args.e_eps]

    while True:
        os.system("cls")
        UserInput = input(
            "1. 查詢ETF成分股 \n2. 查詢個股 \n3. 三大法人買賣超 \n4. 退出 \n輸入: "
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

        # 4. 退出
        elif UserInput == "4":
            break

        else:
            print("Enter Error!!")
            input()
            continue
        for title, StockList in StockLists.items():
            print(title, StockList)

            # Get Data
            calculator(Database, StockList, EPSLists, parameter, new_result / Path(title))
        print("Enter to continue...")
        input()

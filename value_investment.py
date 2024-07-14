import shutil
from termcolor import *
from FinMind.data import DataLoader
import os


from stock_selector.stock_select import getETFConstituent, getInstitutional_TOP50
from calculator.calculator import calculator
from utils.utils import ResultOutput, txt_read, ModifideParameter, Parameter_read


finmind_token = txt_read("token.txt")


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

    if finmind_token == "":
        print("Put the token.txt")
        exit()

    # Load finmind api
    api = DataLoader()
    api.login_by_token(api_token=finmind_token)
    all_stock_info = api.taiwan_stock_info()

    # recreate folder
    if os.path.exists("results"):
        shutil.rmtree("results")
    os.mkdir("results")

    # Read the caculate Parameter
    if os.path.exists("Parameter.txt"):
        parameter = Parameter_read("Parameter.txt")
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
            UserInput = input("1.0050, 0051, 006201\n2. 自行輸入\n輸入: ")
            ETFList = []
            if UserInput == "1":
                ETFList = ["0050", "0051", "006201"]
            elif UserInput == "2":
                ETFList = input("請用空格隔開: ").split(" ")
            for ETF_ID in ETFList:
                StockLists[ETF_ID] = getETFConstituent(all_stock_info, ETF_ID)

        # 2. 查詢個股
        elif UserInput == "2":
            StockLists = {"User_Choice": input("請用空格隔開: ").split(" ")}

        # 3.三大法人買賣超
        elif UserInput == "3":
            StockLists = {
                " Institutional_Investors": getInstitutional_TOP50(all_stock_info)
            }
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
            fw, cw, csvfile = ResultOutput(title)

            # Get Data
            calculator(
                finmind_token,
                api,
                all_stock_info,
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

import shutil
from termcolor import *
from FinMind.data import DataLoader
import os


from stock_selector.stock_select import getETFConstituent, getInstitutional_TOP50
from calculator.calculator import calculator
from utils.utils import ResultOutput, txt_read, write2txt, Parameter_read


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


def ModifideParameter():
    msgList = [
        "EPS year:  (default is 1)\nN: This year\n\t0: N + 0\n\t1: N + 1\n\t2: N + 2",
        "select forward eps value:  (default is 3)\n\t0: high\n\t1: low\n\t2: average\n\t3: medium",
        "Reference how many years: (default is 4.5)",
        "e_eps (default is None):",
    ]
    default = [1, 3, 4.5, None]

    Parameter = []
    with open("Parameter.txt", "w") as pf:
        for i in range(4):
            os.system("cls")
            print(msgList[i])
            UserInput = input("Input: ")
            try:
                Parameter.append(float(UserInput))
            except:
                print(f"Use default Value: {default[i]}")
                Parameter.append(default[i])
            write2txt(Parameter[i], pf)
    return Parameter


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
            csvfile.close()

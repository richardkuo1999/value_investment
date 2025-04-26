import os
import sys
import yaml
from pathlib import Path
import argparse

from Database.finmind import Finminder

sys.path.append(os.path.dirname(__file__))

from utils.utils import load_token
from utils.output import result_output
from calculator.calculator import calculator
from calculator.stock_select import fetch_etf_constituents, fetch_institutional_top50

def parse_arguments():
    parser = argparse.ArgumentParser(description="Stock analysis program")
    parser.add_argument(
        "-level",
        type=int,
        default=4,
        choices=[1, 2, 3, 4],
        help="Forward EPS value (1: high, 2: low, 3: average, 4: medium)"
    )
    parser.add_argument(
        "-year",
        type=float,
        default=4.5,
        help="Data calculation length (years)"
    )
    args = parser.parse_args()
    return [args.level, args.year]

def get_stock_lists(user_input: str) -> dict[str, dict[str]]:
    # 1. 查詢ETF成分股
    if user_input == "1":
        sub_user_input = input("1.0050, 006201, 0051\n2. 自行輸入\n輸入: ")
        StockLists = {}
        etf_list = None
        if sub_user_input == "1":
            etf_list = ["0050", "006201", "0051"]
        elif sub_user_input == "2":
            etf_list = input("請用空格隔開: ").split()
        for etf in etf_list:
            StockLists[etf] = fetch_etf_constituents(etf)
        return StockLists

    # 2. 查詢個股
    elif user_input == "2":
        return {"User_Choice": input("請用空格隔開: ").split()}

    # 3.三大法人買賣超
    elif user_input == "3":
        return {" Institutional_Investors": fetch_institutional_top50()}

    # 4. 退出
    elif user_input == "4":
        return None

if __name__ == "__main__":
    new_result = Path("results")
    eps_lists = None  # set your EST eps in here
    
    token = load_token()
    db = Finminder(token)

    # create folder
    new_result.mkdir(parents=True, exist_ok=True)

    # Read the caculate Parameter
    params = parse_arguments()

    while True:
        os.system("cls")
        user_input = input(
            "1. 查詢ETF成分股 \n2. 查詢個股 \n3. 三大法人買賣超 \n4. 退出 \n輸入: "
        )
        stock_lists = get_stock_lists(user_input)
        print(stock_lists)

        if not stock_lists:
            break

        for title, stock_list in stock_lists.items():
            print(title, stock_list)

            # Get Data
            StockDatas = calculator(db, stock_list, params)
            result_output(new_result / Path(title), StockDatas, eps_lists)
        print("Enter to continue...")
        input()

import os
import sys
import logging
import aiohttp
import asyncio
import argparse
from pathlib import Path


sys.path.append(os.path.dirname(__file__))

from utils.utils import logger, load_token
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
        help="Forward EPS value (1: high, 2: low, 3: average, 4: medium)",
    )
    parser.add_argument(
        "-year", type=float, default=4.5, help="Data calculation length (years)"
    )
    args = parser.parse_args()
    return [args.level, args.year]


def get_stock_lists(session, user_input: str):
    try:
        if user_input == "1":  # 查詢 ETF 成分股
            sub_user_input = input("1. 0050, 006201, 0051\n2. 自行輸入\n輸入: ")
            stock_lists = {}
            etf_list = None
            if sub_user_input == "1":
                etf_list = ["0050", "006201", "0051"]
            elif sub_user_input == "2":
                etf_list = input("請用空格隔開: ").strip().split()
            else:
                print("無效的子選項")
                return None
            for etf in etf_list:
                stock_lists[etf] = fetch_etf_constituents(session, etf)
            return stock_lists

        elif user_input == "2":  # 查詢個股
            stocks = input("請用空格隔開: ").strip().split()
            if not stocks:
                logger.error("未提供股票代碼")
                return None
            return {"User_Choice": stocks}

        elif user_input == "3":  # 三大法人買賣超
            return {"Institutional_Investors": fetch_institutional_top50(session)}

        elif user_input == "4":  # 退出
            raise KeyboardInterrupt

        else:
            logger.error("無效的輸入選項")
            return None
    except Exception as e:
        logger.error(f"獲取股票列表失敗：{e}")
        return None


async def main():
    tokens = load_token()
    params = parse_arguments()
    new_result = Path("results")
    new_result.mkdir(parents=True, exist_ok=True)
    eps_lists = None  # 可根據需求設置預測 EPS

    while True:
        try:
            # 跨平台清屏
            print("\033[H\033[J", end="")
            user_input = input(
                "1. 查詢 ETF 成分股\n2. 查詢個股\n3. 三大法人買賣超\n4. 退出\n輸入: "
            )
            async with aiohttp.ClientSession() as session:
                stock_lists = get_stock_lists(session, user_input)
                if not stock_lists:
                    break

                print(f"股票列表: {stock_lists}")
                for title, stock_list in stock_lists.items():
                    print(f"處理 {title}: {stock_list}")
                    try:
                        stock_data = await calculator(session, stock_list, params, tokens)
                        result_output(new_result / Path(title), stock_data, eps_lists)
                    except Exception as e:
                        logger.error(f"處理 {title} 失敗：{e}")

            input("按 Enter 繼續...")
        except KeyboardInterrupt:
            print("用戶終止程式")
            break
        except Exception as e:
            logger.error(f"主循環錯誤：{e}")
            input("發生錯誤，請重試...")
        finally:
            logging.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

import yaml
import sys
import requests
from datetime import datetime, timedelta


from utils.utils import Line_print


def NotifyCnnFearGreedIndex(Database):
    start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    FearGreedData = Database.getCnnFearGreedIndex(start_date).iloc[-1]
    Line_print(
        "\nCNN Fear & Greed Index: \ndate: {}\nfear_greed: {}\nfear_greed_emotion: {}".format(
            FearGreedData['date'],
            FearGreedData['fear_greed'],
            FearGreedData['fear_greed_emotion'],
        )
    )


def NotifyOptionSupportPressure(Database):
    start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    option_id = "TXO"

    df = Database.get_taiwan_option_daily(option_id, start_date)
    date = df.iloc[-1]['date']
    df = df[df['date'] == date]
    ContractDate_list = df['contract_date'].unique().tolist()
    msgs = f"\n台指期選擇權支撐、壓力\n台灣加權指數:{Database.get_TAIEX('2024-11-28').iloc[-1]['TAIEX']}\n\n"
    for contract_date in ContractDate_list:
        call = df[(df['contract_date'] == contract_date) & (df['call_put'] == "call")]
        call_sum = call.groupby(['strike_price'])['open_interest'].sum()
        callPrice, callVal = call_sum.idxmax(), call_sum.max()

        put = df[(df['contract_date'] == contract_date) & (df['call_put'] == "put")]
        put_sum = put.groupby(['strike_price'])['open_interest'].sum()
        putPrice, putVal = put_sum.idxmax(), put_sum.max()

        msgs += f"到期月份:{contract_date:<10}\n"
        msgs += f"支撐: {putPrice:.0f}/{putVal:<5}價/口\n"
        msgs += f"壓力: {callPrice:.0f}/{callVal:<5}價/口\n\n"
    Line_print(msgs)

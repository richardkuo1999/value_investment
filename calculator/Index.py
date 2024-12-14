from datetime import datetime, timedelta
from utils.utils import Line_print


def CnnFearGreedIndex(Database):
    start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    fear_greed_data = Database.get_cnn_fear_greed_index(start_date).iloc[-1]

    msgs = "\nCNN Fear & Greed Index:"
    msgs += f"\ndate: {fear_greed_data['date']}"
    msgs += f"\nfear_greed: {fear_greed_data['fear_greed']}"
    msgs += f"\nfear_greed_emotion: {fear_greed_data['fear_greed_emotion']}"
    return msgs


def OptionSupportPressure(Database):
    start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    option_id = "TXO"

    def get_latest_option_data(database, option_id, start_date):
        df = database.get_taiwan_option_daily(option_id, start_date)
        latest_date = df.iloc[-1]["date"]
        return df[df["date"] == latest_date]

    def get_max_interest_price(df, contract_date, call_put):
        filtered_df = df[
            (df["contract_date"] == contract_date) & (df["call_put"] == call_put)
        ]
        interest_sum = filtered_df.groupby(["strike_price"])["open_interest"].sum()
        return interest_sum.idxmax(), interest_sum.max()

    def format_contract_info(contract_date, put_price, put_val, call_price, call_val):
        return (
            f"到期月份:{contract_date:<10}\n"
            f"支撐: {put_price:.0f}/{put_val:<5}價/口\n"
            f"壓力: {call_price:.0f}/{call_val:<5}價/口\n\n"
        )

    df = get_latest_option_data(Database, option_id, start_date)
    contract_dates = df["contract_date"].unique().tolist()

    current_taiex = Database.get_taiex("2024-11-28").iloc[-1]["TAIEX"]
    msgs = f"\n台指期選擇權支撐、壓力\n台灣加權指數:{current_taiex}\n\n"

    for contract_date in contract_dates:
        call_price, call_val = get_max_interest_price(df, contract_date, "call")
        put_price, put_val = get_max_interest_price(df, contract_date, "put")
        msgs += format_contract_info(
            contract_date, put_price, put_val, call_price, call_val
        )
    return msgs


def NotifyMacroeconomics(Database):
    Line_print(CnnFearGreedIndex(Database))
    Line_print(OptionSupportPressure(Database))

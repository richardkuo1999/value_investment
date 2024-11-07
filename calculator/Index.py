import yaml
import sys
import requests
from datetime import datetime, timedelta


from utils.utils import Line_print


def NotifyCnnFearGreedIndex(Database):
    start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    FearGreedData = Database.getCnnFearGreedIndex(start_date, end_date)
    last_day = FearGreedData.shape[1] - 1
    Line_print(
        "\nCNN Fear & Greed Index: \ndate: {}\nfear_greed: {}\nfear_greed_emotion: {}".format(
            FearGreedData["date"][last_day],
            FearGreedData["fear_greed"][last_day],
            FearGreedData["fear_greed_emotion"][last_day],
        )
    )

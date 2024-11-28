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
            FearGreedData["date"],
            FearGreedData["fear_greed"],
            FearGreedData["fear_greed_emotion"],
        )
    )

import sys
import csv
import signal
import shutil
import datetime
import tkinter as tk
import numpy as np
import statistics
from termcolor import *
from FinMind.data import DataLoader
import os
import time
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import urllib.request
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates  # 處理日期
import pandas as pd
from sklearn import linear_model
import plotly.graph_objects as go
from enum import Enum
from bs4 import BeautifulSoup

from stock_selector.stock_select import getETFConstituent, getInstitutional_TOP50
from calculator.calculator import calculator
from utils.utils import ResultOutput


finmind_token = ""

with open("token.txt", "r") as f:
    finmind_token = f.read()


sel = 1
level = 4
year = 4.5
e_eps = None

if __name__ == "__main__":

    if finmind_token == "":
        print("Put the token.txt")
        exit()

    api = DataLoader()
    api.login_by_token(api_token=finmind_token)
    all_stock_info = api.taiwan_stock_info()
    
    if os.path.exists("results"):
        shutil.rmtree("results")
    os.mkdir("results")

    while True:
        UserInput = input(
            "1.查詢ETF成分股\n2. 查詢個股\n3.三大法人買賣超\n4. 退出\n輸入: "
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

        # 4. 退出
        elif UserInput == "4":
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
                year,
                sel,
                level,
                e_eps,
                fw,
                cw,
            )

            fw.close()
            csvfile.close()

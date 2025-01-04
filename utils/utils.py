import csv
import yaml
import requests
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
}


def fetch_webpage(url: str, headers=headers) -> BeautifulSoup:
    """Fetch and parse webpage content"""
    response = requests.get(url, headers=headers)
    response.encoding = "utf-8"
    return BeautifulSoup(response.text, "html5lib")


def txt_read(file: Path) -> str:
    txtdata = file.read_text()
    return txtdata


def write2txt(msg, filepath=None):
    with filepath.open(mode="a", encoding="utf-8") as file:
        file.write(f"{msg}\n")
    print(msg)


def write2csv(result_path, csvdata):
    with open(result_path, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(csvdata)


def dict2list(data):
    result = []
    for key, value in data.items():
        if isinstance(value, dict):
            result.extend(dict2list(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    result.extend(dict2list(item))
                else:
                    result.append(item)
        else:
            result.append(value)
    return result


def Line_print(msg):
    print(msg)

    with open("token.yaml", "r") as file:
        Token = yaml.safe_load(file)

    url = "https://notify-api.line.me/api/notify"
    token = Token["LineToken"]
    headers = {"Authorization": "Bearer " + token}
    data = {"message": msg}
    data = requests.post(url, headers=headers, data=data)


def upload_files(folder_path, yamlToken, gdToken):

    SCOPES = ["https://www.googleapis.com/auth/drive"]

    # 建立憑證
    creds = service_account.Credentials.from_service_account_file(
        gdToken, scopes=SCOPES
    )

    # 串連服務
    service = build("drive", "v3", credentials=creds)

    for filename in folder_path.iterdir():
        # print(filename)

        foldID = yamlToken["new_result"]
        media = MediaFileUpload(str(filename))
        file = {"name": filename.name, "parents": [foldID]}
        file_id = service.files().create(body=file, media_body=media).execute()


def isOrdinaryStock(StockID):
    return StockID[0] in "12345678"


def getLasturl(csvpath):
    data = {}
    if csvpath.is_file() and csvpath.suffix == ".csv":
        df = pd.read_csv(csvpath, encoding="utf-8")

        # Skip header row and convert directly to dict
        for _, row in df.iterrows():
            data[str(row["代號"])] = {
                "DataTime": datetime.strptime(row["資料時間"], "%Y/%m/%d"),
                "url": row["ANUEurl"],
            }
    return data


def getProfit(targetPrice, Price):
    return float(targetPrice / Price - 1) * 100


def getTarget(rate, data):
    return rate * data


class UnderEST:
    @staticmethod
    def getUnderstimated(StockData):
        UndersESTDict = {}
        for index, (StockID, StockData) in enumerate(StockData.items()):
            if UnderEST.isUnderstimated(StockData):
                UndersESTDict.update({StockID: StockData})
        return UndersESTDict

    @staticmethod
    def NotifyUndersEST(UndersESTDict):
        msg = "Under Stimated\n"
        for No, (StockID, StockData) in enumerate(UndersESTDict.items(), start=0):
            msg += f"{StockData['代號']}{StockData['名稱']}: {UnderEST.get_expProfit(StockData):.1f}%\n"
        Line_print(msg)
        return msg

    @staticmethod
    def isUnderstimated(StockData):
        return UnderEST.get_expProfit(StockData) > 0.0

    @staticmethod
    def get_expProfit(StockData):
        eps = StockData["Anue"]["EPS(EST)"] if StockData["Anue"]["EPS(EST)"] else StockData["EPS(TTM)"]
        return getProfit(getTarget(StockData["SDESTPER"][4], eps), StockData["價格"])

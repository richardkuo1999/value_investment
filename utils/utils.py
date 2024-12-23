import os
import csv
import yaml
import requests
import numpy as np
import pandas as pd
from enum import Enum
from pathlib import Path
from bs4 import BeautifulSoup
from googlesearch import search
from urllib.parse import unquote

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def txt_read(file: Path) -> str:
    txtdata = file.read_text()
    return txtdata


default_Parameter = [3, 4.5, None]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
}


def write2txt(msg, filepath=None):
    with filepath.open(mode="a", encoding="utf-8") as file:
        file.write(f"{msg}\n")
    print(msg)


def fetch_webpage(url: str, headers=headers) -> BeautifulSoup:
    """Fetch and parse webpage content"""
    response = requests.get(url, headers=headers)
    response.encoding = "utf-8"
    return BeautifulSoup(response.text, "html5lib")


def ResultOutput(result_path, StockDatas):
    rowtitle = [
        "股票名稱",
        "股票代號",
        "公司產業",
        "價格",
        "股票類型",
        # 5
        "往上機率",
        "區間震盪機率",
        "往下機率",
        "TL價",
        "TL潛在漲幅",
        # 10
        "保守做多期望值",
        "保守做多報酬率",
        "樂觀做多期望值",
        "樂觀做多報酬率",
        "樂觀做空期望值：",
        "樂觀做空報酬率：",
        # 16
        "估計EPS",
        "預估本益比",
        "Factest目標價",
        "Factest預估價潛在漲幅",
        "資料時間",
        # 21
        "PER25%",
        "PER25%價位",
        "PER25%潛在漲幅",
        "PER50%",
        "PER50%價位",
        "PER50%潛在漲幅",
        "PER75%",
        "PER75%價位",
        "PER75%潛在漲幅",
        "PER平均",
        "PER平均價位",
        "PER平均潛在漲幅",
        # 33
        "PER_TL+3SD PE",
        "PER_TL+3SD價位",
        "PER_TL+3SD在漲幅",
        "PER_TL+2SD PE",
        "PER_TL+2SD價位",
        "PER_TL+2SD在漲幅",
        "PER_TL+SD PE",
        "PER_TL+SD價位",
        "PER_TL+SD潛在漲幅",
        "PER_TL0SD PE",
        "PER_TL0SD價位",
        "PER_TL0SD潛在漲幅",
        "PER_TL-SD PE",
        "PER_TL-SD價位",
        "PER_TL-SD潛在漲幅",
        "PER_TL-2SD PE",
        "PER_TL-2SD價位",
        "PER_TL-2SD潛在漲幅",
        "PER_TL-3SD PE",
        "PER_T-3SD價位",
        "PER_TL-3SD潛在漲幅",
        # 54
        "公司資訊",
        "PEG",
        "PEG PE",
        "PEG價位",
        "PEG潛在漲幅",
        # 59
        "PBR25%",
        "PBR25%價位",
        "PBR25%潛在漲幅",
        "PBR50%",
        "PBR50%價位",
        "PBR50%潛在漲幅",
        "PBR75%",
        "PBR75%價位",
        "PBR75%潛在漲幅",
        "PBR平均",
        "PBR平均價位",
        "PBR平均潛在漲幅",
        # 71
        "PBR_TL+3SD PE",
        "PBR_TL+3SD價位",
        "PBR_TL+3SD在漲幅",
        "PBR_TL+2SD PE",
        "PBR_TL+2SD價位",
        "PBR_TL+2SD在漲幅",
        "PBR_TL+SD PE",
        "PBR_TL+SD價位",
        "PBR_TL+SD潛在漲幅",
        "PBR_TL0SD PE",
        "PBR_TL0SD價位",
        "PBR_TL0SD潛在漲幅",
        "PBR_TL-SD PE",
        "PBR_TL-SD價位",
        "PBR_TL-SD潛在漲幅",
        "PBR_TL-2SD PE",
        "PBR_TL-2SD價位",
        "PBR_TL-2SD潛在漲幅",
        "PBR_TL-3SD PE",
        "PBR_T-3SD價位",
        "PBR_TL-3SD潛在漲幅",
        # 92
    ]
    for No, (StockID, StockData) in enumerate(StockDatas.items(), start=0):
        if No == 0:
            continue
        csvdata = [None] * 92
        fw = result_path.with_suffix(".txt")
        write2txt(
            "===========================================================================\n",
            fw,
        )

        write2txt(
            f"股票名稱: {StockData['Name']}\t\t股票代號: {StockData['stock_id']}\
                    \n公司產業: {StockData['industry_category']}\t\t股票類型: {StockData['IPOtype']}",
            fw,
        )

        write2txt(f"公司資訊:{StockData['companyinfo']}\n\n", fw)
        csvdata[54] = StockData["companyinfo"]

        write2txt(f"現在股價為:	{StockData['price']}\n", fw)

        csvdata[0], csvdata[1], csvdata[2], csvdata[3], csvdata[4] = (
            StockData["Name"],
            StockData["stock_id"],
            StockData["industry_category"],
            StockData["price"],
            StockData["IPOtype"],
        )

        write2txt(
            "===========================================================================",
            fw,
        )
        write2txt("計算股價均值回歸......\n", fw)
        write2txt(
            "均值回歸適合使用在穩定成長的股票上，如大盤or台積電等，高速成長及景氣循環股不適用，請小心服用。",
            fw,
        )
        write2txt("偏離越多標準差越遠代表趨勢越強，請勿直接進場。\n\n", fw)

        write2txt(
            f"{StockData['stock_id']} 往上的機率為: {StockData['mean_reversion'][0][0]}%, 維持在這個區間的機率為: {StockData['mean_reversion'][0][1]}%, 往下的機率為: {StockData['mean_reversion'][0][2]}%\n",
            fw,
        )
        write2txt(
            f"目前股價: {StockData['price']}, TL價: {StockData['mean_reversion'][1][0]}, TL價潛在漲幅: {StockData['mean_reversion'][1][1]}",
            fw,
        )
        write2txt("做多評估：", fw)
        write2txt(
            f"期望值為: {StockData['mean_reversion'][2][0]}, 期望報酬率為: {StockData['mean_reversion'][2][1]}% (保守計算: 上檔TL，下檔歸零)",
            fw,
        )
        write2txt(
            f"期望值為: {StockData['mean_reversion'][3][0]}, 期望報酬率為: {StockData['mean_reversion'][3][1]}% (樂觀計算: 上檔TL，下檔-3SD)\n",
            fw,
        )
        write2txt("做空評估: ", fw)
        write2txt(
            f"期望值為: {StockData['mean_reversion'][4][0]}, 期望報酬率為: {StockData['mean_reversion'][4][1]}% (樂觀計算: 上檔+3SD，下檔TL)\n",
            fw,
        )

        csvdata[5], csvdata[6], csvdata[7], csvdata[8], csvdata[9] = (
            StockData["mean_reversion"][0][0],
            StockData["mean_reversion"][0][1],
            StockData["mean_reversion"][0][2],
            StockData["mean_reversion"][1][0],
            StockData["mean_reversion"][1][1],
        )

        csvdata[10], csvdata[11], csvdata[12], csvdata[13], csvdata[14], csvdata[15] = (
            StockData["mean_reversion"][2][0],
            StockData["mean_reversion"][2][1],
            StockData["mean_reversion"][3][0],
            StockData["mean_reversion"][3][1],
            StockData["mean_reversion"][4][0],
            StockData["mean_reversion"][4][1],
        )

        write2txt(
            "===========================================================================",
            fw,
        )
        write2txt("Factest預估", fw)
        write2txt("", fw)
        if StockData["EPSeveryear"]:
            for line in StockData["EPSeveryear"]:
                write2txt(line, fw)
        else:
            write2txt(f"無法取得 Fectset EPS 評估報告，使用近四季EPS總和.\n", fw)
        write2txt(
            f"\n估計EPS: {StockData['Anue']['ESTeps']}  預估本益比：    {StockData['Anue']['FuturePER']}",
            fw,
        )
        write2txt(
            f"Factest目標價: {StockData['Anue']['FactsetESTprice'][0]}  推算潛在漲幅為:  {StockData['Anue']['FactsetESTprice'][1]}",
            fw,
        )
        write2txt(f"資料日期: {StockData['Anue']['DataTime']}  ", fw)
        write2txt("", fw)

        csvdata[16], csvdata[17], csvdata[18], csvdata[19], csvdata[20] = (
            StockData["Anue"]["ESTeps"],
            StockData["Anue"]["FuturePER"],
            StockData["Anue"]["FactsetESTprice"][0],
            StockData["Anue"]["FactsetESTprice"][1],
            StockData["Anue"]["DataTime"],
        )

        write2txt(
            "===========================================================================",
            fw,
        )
        write2txt("計算本益比四分位數與平均本益比......", fw)
        write2txt("", fw)
        uniformat = (
            "本益比{}% 為:\t{:<20.2f} 推算價位為:\t{:<20.2f} 推算潛在漲幅為:\t{:.2f}%"
        )
        for i in range(3):
            write2txt(
                uniformat.format(
                    25 * (i + 1),
                    StockData["ESTPER"][i][0],
                    StockData["ESTPER"][i][1],
                    StockData["ESTPER"][i][2],
                ),
                fw,
            )
            csvdata[21 + 3 * i], csvdata[22 + 3 * i], csvdata[23 + 3 * i] = (
                StockData["ESTPER"][i][0],
                StockData["ESTPER"][i][1],
                StockData["ESTPER"][i][2],
            )
        write2txt(
            uniformat.format(
                "平均",
                StockData["ESTPER"][3][0],
                StockData["ESTPER"][3][1],
                StockData["ESTPER"][3][2],
            ),
            fw,
        )
        csvdata[30], csvdata[31], csvdata[32] = (
            StockData["ESTPER"][3][0],
            StockData["ESTPER"][3][1],
            StockData["ESTPER"][3][2],
        )
        write2txt("", fw)

        write2txt(
            "===========================================================================",
            fw,
        )
        write2txt("計算本益比標準差......", fw)
        write2txt("", fw)
        uniformat = "{:<20} {:<20.2f} 推算價位為:\t{:<20.2f} 推算潛在漲幅為:\t{:.2f}%"
        for i, title in enumerate(["+3", "+2", "+1", "", "-1", "-2", "-3"]):
            write2txt(
                uniformat.format(
                    f"TL{title}SD",
                    StockData["SDESTPER"][i][0],
                    StockData["SDESTPER"][i][1],
                    StockData["SDESTPER"][i][2],
                ),
                fw,
            )
            csvdata[33 + 3 * i], csvdata[34 + 3 * i], csvdata[35 + 3 * i] = (
                StockData["SDESTPER"][i][0],
                StockData["SDESTPER"][i][1],
                StockData["SDESTPER"][i][2],
            )
        write2txt(
            "===========================================================================",
            fw,
        )

        write2txt("計算股價淨值比四分位數與平均本益比......", fw)
        write2txt("", fw)
        uniformat = "股價淨值比{}% 為:\t{:<20.2f} 推算價位為:\t{:<20.2f} 推算潛在漲幅為:\t{:.2f}%"
        for i in range(3):
            write2txt(
                uniformat.format(
                    25 * (i + 1),
                    StockData["ESTPBR"][i][0],
                    StockData["ESTPBR"][i][1],
                    StockData["ESTPBR"][i][2],
                ),
                fw,
            )
            csvdata[59 + 3 * i], csvdata[60 + 3 * i], csvdata[61 + 3 * i] = (
                StockData["ESTPBR"][i][0],
                StockData["ESTPBR"][i][1],
                StockData["ESTPBR"][i][2],
            )
        write2txt(
            uniformat.format(
                "平均",
                StockData["ESTPBR"][3][0],
                StockData["ESTPBR"][3][1],
                StockData["ESTPBR"][3][2],
            ),
            fw,
        )
        csvdata[68], csvdata[69], csvdata[70] = (
            StockData["ESTPBR"][3][0],
            StockData["ESTPBR"][3][1],
            StockData["ESTPBR"][3][2],
        )
        write2txt("", fw)

        write2txt(
            "===========================================================================",
            fw,
        )
        write2txt("計算股價淨值比標準差......", fw)
        write2txt("", fw)
        uniformat = "{:<20} {:<20.2f} 推算價位為:\t{:<20.2f} 推算潛在漲幅為:\t{:.2f}%"
        for i, title in enumerate(["+3", "+2", "+1", "", "-1", "-2", "-3"]):
            write2txt(
                uniformat.format(
                    f"TL{title}SD",
                    StockData["SDESTPBR"][i][0],
                    StockData["SDESTPBR"][i][1],
                    StockData["SDESTPBR"][i][2],
                ),
                fw,
            )
            csvdata[71 + 3 * i], csvdata[72 + 3 * i], csvdata[73 + 3 * i] = (
                StockData["SDESTPBR"][i][0],
                StockData["SDESTPBR"][i][1],
                StockData["SDESTPBR"][i][2],
            )
        write2txt(
            "===========================================================================",
            fw,
        )

        csvdata[55], csvdata[56], csvdata[57], csvdata[58] = StockData["PEG"]

        write2txt("PEG估值......", fw)
        write2txt("", fw)
        uniformat = "PEG: {:<20.2f} 本益比為:{:<20.2f} 推算價位為:\t{:<20.2f} 推算潛在漲幅為:\t{:.2f}%"
        write2txt(
            uniformat.format(
                StockData["PEG"][0],
                StockData["PEG"][1],
                StockData["PEG"][2],
                StockData["PEG"][3],
            ),
            fw,
        )

        write2txt(
            "===========================================================================",
            fw,
        )

        with open(
            result_path.with_suffix(".csv"), mode="a", newline="", encoding="utf-8"
        ) as file:
            writer = csv.writer(file)
            if No == 1:
                writer.writerow(rowtitle)
            writer.writerow(csvdata)

        # csvdata[3] = (
        #     f'=STOCK(CONCAT(B{No+1},"{".two" if csvdata[4]=="tpex" else ".tw"}"))'
        # )
        # csvdata[9] = f"=(I{No+1}/D{No+1}-1)*100"
        # csvdata[19] = f"=(S{No+1}/D{No+1}-1)*100"

        # csvdata[23], csvdata[26], csvdata[29], csvdata[32] = (
        #     f"=(W{No+1}/D{No+1}-1)*100",
        #     f"=(Z{No+1}/D{No+1}-1)*100",
        #     f"=(AC{No+1}/D{No+1}-1)*100",
        #     f"=(AF{No+1}/D{No+1}-1)*100",
        # )

        # (
        #     csvdata[35],
        #     csvdata[38],
        #     csvdata[41],
        #     csvdata[44],
        #     csvdata[47],
        #     csvdata[50],
        #     csvdata[53],
        # ) = (
        #     f"=(AI{No+1}/D{No+1}-1)*100",
        #     f"=(AL{No+1}/D{No+1}-1)*100",
        #     f"=(AO{No+1}/D{No+1}-1)*100",
        #     f"=(AR{No+1}/D{No+1}-1)*100",
        #     f"=(AU{No+1}/D{No+1}-1)*100",
        #     f"=(AX{No+1}/D{No+1}-1)*100",
        #     f"=(BA{No+1}/D{No+1}-1)*100",
        # )
        # csvdata[56], csvdata[57] = (
        #     f"=(D{No+1}/BD{No+1}/Q{No+1})",
        #     f"=(D{No+1}/BD{No+1})",
        # )

        # with open(
        #     result_path.with_name(result_path.stem + "_apple").with_suffix(".csv"),
        #     mode="a",
        #     newline="",
        #     encoding="utf-8",
        # ) as file:
        #     writer = csv.writer(file)
        #     if No == 1:
        #         writer.writerow(rowtitle)
        #     writer.writerow(csvdata)

        # csvdata[4] = "".join(
        #     [
        #         '=IMPORTXML(CONCATENATE("https://tw.stock.yahoo.com/quote/",B{},".TWO"),'.format(
        #             No + 1
        #         ),
        #         '"//*[@id=""main-0-QuoteHeader-Proxy""]/div/div[2]/div[1]/div/span[1]")',
        #     ]
        # )
        # with open(
        #     result_path.with_name(result_path.stem + "_google").with_suffix(".csv"),
        #     mode="a",
        #     newline="",
        #     encoding="utf-8",
        # ) as file:
        #     writer = csv.writer(file)
        #     if No == 1:
        #         writer.writerow(rowtitle)
        #     writer.writerow(csvdata)


def get_search_results(query, num_results=10):
    search_results = []
    # url = f"https://www.google.com/search?q={query}&num={num_results}"
    url = f"https://tw.search.yahoo.com/search?p={query}&fr=yfp-search-sb"
    soup = fetch_webpage(url)

    # For Google engine 1
    # search_results.extend(
    #     [data.find("a")["href"] for data in soup.find_all("div", class_="g")]
    # )

    # For Google engine 2
    # search_results = search(query, stop=num_results, pause=2.0)

    # For Yahoo engine
    for i in (soup.find_all("div", id="left")[0]).find_all("a"):
        url = i["href"]
        if "https%3a%2f%2fnews.cnyes.com%2fnews%2fid%2f" in url:
            search_results.append(unquote(url.split("/RK=")[0].split("RU=")[1]))

    return search_results


def Parameter_read(file):
    txtdata = txt_read(file).split("\n")
    try:
        level = int(txtdata[0])
        year = float(txtdata[1])
        e_eps = float(txtdata[2]) if txtdata[2].lower() != "none" else None
    except:
        level, year, e_eps = default_Parameter
    return [level, year, e_eps]


"""
parameter -> sel
# Description: EPS year
# # N: This year
# # 0: N + 0
# # 1: N + 1
# # 2: N + 2

parameter -> level
Description: select forward eps value
# 0: high, 1: low, 2: average, 3: medium
"""


def ModifideParameter() -> list:
    msgList = [
        # "EPS year:  (default is 1)\nN: This year\n\t0: N + 0\n\t1: N + 1\n\t2: N + 2",
        "select forward eps value:  (default is 3)\n\t0: high\n\t1: low\n\t2: average\n\t3: medium",
        "Reference how many years: (default is 4.5)",
        "e_eps (default is None):",
    ]
    float_input = [2, 3]

    Parameter = []
    with open("Parameter.txt", "w") as pf:
        for i in range(3):
            os.system("cls")
            print(msgList[i])
            UserInput = input("Input: ")
            try:
                if i in float_input:
                    Parameter.append(float(UserInput))
                else:
                    Parameter.append(int(UserInput))
            except:
                print(f"Use default Value: {default_Parameter[i]}")
                Parameter.append(default_Parameter[i])
                input()
            write2txt(Parameter[i], pf)

        print(f"your Parameter: {Parameter}")
        input()
    return Parameter


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


class UnderEST:
    @staticmethod
    def getUnderstimated(StockData):
        UndersESTDict = {"test": 0}
        for index, (StockID, StockData) in enumerate(StockData.items()):
            if not isOrdinaryStock(StockID):
                continue
            if float(StockData["SDESTPER"][4][2]) > 0.0:
                UndersESTDict.update({StockID: StockData})
        return UndersESTDict

    @staticmethod
    def NotifyUndersEST(UndersESTDict):
        msg = "Under Stimated\n"
        for No, (StockID, StockData) in enumerate(UndersESTDict.items(), start=0):
            if No == 0:
                continue
            msg += f"{StockData['stock_id']}{StockData['Name']}: {StockData['SDESTPER'][4][2]:.1f}%\n"
        Line_print(msg)
        return msg


def isOrdinaryStock(StockID):
    return StockID[0] in "12345678"

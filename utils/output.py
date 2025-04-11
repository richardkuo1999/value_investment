import csv

from utils.utils import write2txt, dict2list, write2csv, getProfit, getTarget


rowtitle = [
    "名稱",
    "代號",
    "產業",
    "資訊",
    "交易所",
    "價格",
    # =========== 6
    "EPS(TTM)",
    "BPS",
    "PE(TTM)",
    "PB(TTM)",
    # =========== 10
    "Yahoo_1yTargetEst",
    # =========== 11
    "EPS(EST)",
    "PE(EST)",
    "Factest目標價",
    "資料時間",
    "ANUEurl",
    # =========== 16
    "往上機率",
    "區間震盪機率",
    "往下機率",
    "TL價",
    "保守做多期望值",
    "樂觀做多期望值",
    "樂觀做空期望值",
    # =========== 23
    "超極樂觀",
    "極樂觀",
    "樂觀",
    "趨勢",
    "悲觀",
    "極悲觀",
    "超極悲觀",
    # ===========
    "PE(25%)",
    "PE(50%)",
    "PE(75%)",
    "PE(平均)",
    "PE(TL+3SD)",
    "PE(TL+2SD)",
    "PE(TL+SD)",
    "PE(TL)",
    "PE(TL-SD)",
    "PE(TL-2SD)",
    "PE(TL-3SD)",
    # ===========
    "PB(25%)",
    "PB(50%)",
    "PB(75%)",
    "PB(平均)",
    "PB(TL+3SD)",
    "PB(TL+2SD)",
    "PB(TL+SD)",
    "PB(TL)",
    "PB(TL-SD)",
    "PB(TL-2SD)",
    "PB(TL-3SD)",
    # ===========
    "PEG",
]


def csvOutput(result_path, StockDatas):
    result_path = result_path.with_suffix(".csv")
    write2csv(result_path, rowtitle)
    for No, (StockID, StockData) in enumerate(StockDatas.items()):
        write2csv(result_path, dict2list(StockData))


def txtOutput(result_path, StockDatas, EPSLists=None):
    for No, (StockID, StockData) in enumerate(StockDatas.items()):
        text = ""
        fw = result_path.with_suffix(".txt")
        ClossPrice = StockData["價格"]
        if EPSLists and EPSLists[No]:
            eps = EPSLists[No]
        eps = (
            StockData["Anue"]["EPS(EST)"]
            if StockData["Anue"]["EPS(EST)"]
            else StockData["EPS(TTM)"]
        )
        bps = StockData["BPS"]

        text += f"""
============================================================================

股票名稱: {StockData["名稱"]}		股票代號: {StockData["代號"]}                    
公司產業: {StockData["產業"]}		交易所: {StockData["交易所"]}
公司資訊: {StockData["資訊"]}

目前股價: {ClossPrice:>10.2f}
EPS(TTM): {StockData["EPS(TTM)"]:>10.2f}          BPS: {bps:>10.2f}
PE(TTM): {StockData["PE(TTM)"]:>10.2f}          PB(TTM): {StockData["PB(TTM)"]:>10.2f}
"""

        TargetPrice = StockData["Yahoo_1yTargetEst"]
        if TargetPrice:
            Profit = getProfit(TargetPrice, ClossPrice)
            text += f"""
============================================================================
Yahoo Finance 1y Target Est....

目標價位: {TargetPrice:>10.2f}          潛在漲幅: {Profit:>10.2f}%
"""
        else:
            pass

        expect = StockData["MeanReversion"]["expect"]
        prob = StockData["MeanReversion"]["prob"]
        TargetPrice = StockData["MeanReversion"]["TL"]
        Profit = getProfit(TargetPrice, ClossPrice)
        expectProfitRate = [expect[i] / ClossPrice * 100 for i in range(3)]
        text += f"""
============================================================================
股價均值回歸......

均值回歸適合使用在穩定成長的股票上，如大盤or台積電等，高速成長及景氣循環股不適用，請小心服用。
偏離越多標準差越遠代表趨勢越強，請勿直接進場。

{StockData["代號"]} 往上的機率為: {prob[0]:>10.2f}%, 維持在這個區間的機率為: {prob[1]:>10.2f}%, 往下的機率為: {prob[2]:>10.2f}%

目前股價: {ClossPrice:>10.2f}, TL價: {StockData["MeanReversion"]["TL"]:>10.2f}, TL價潛在漲幅: {Profit:>10.2f}
做多評估：
期望值為: {expect[0]:>10.2f}, 期望報酬率為: {expectProfitRate[0]:>10.2f}% (保守計算: 上檔TL，下檔歸零)
期望值為: {expect[1]:>10.2f}, 期望報酬率為: {expectProfitRate[1]:>10.2f}% (樂觀計算: 上檔TL，下檔-3SD)

做空評估: 
期望值為: {expect[2]:>10.2f}, 期望報酬率為: {expectProfitRate[2]:>10.2f}% (樂觀計算: 上檔+3SD，下檔TL)
"""

        TargetPrice = StockData["MeanReversion"]["staff"]
        Profit = [getProfit(TargetPrice[i], ClossPrice) for i in range(7)]
        text += f"""
============================================================================
樂活五線譜......      


    超極樂觀價位: {TargetPrice[0]:>10.2f}, 潛在漲幅: {Profit[0]:>10.2f}%
    極樂觀價位:   {TargetPrice[1]:>10.2f}, 潛在漲幅: {Profit[1]:>10.2f}%
    樂觀價位:     {TargetPrice[2]:>10.2f}, 潛在漲幅: {Profit[2]:>10.2f}%
    趨勢價位:     {TargetPrice[3]:>10.2f}, 潛在漲幅: {Profit[3]:>10.2f}%
    悲觀價位:     {TargetPrice[4]:>10.2f}, 潛在漲幅: {Profit[4]:>10.2f}%
    極悲觀價位:    {TargetPrice[5]:>10.2f}, 潛在漲幅: {Profit[5]:>10.2f}%
    超極悲觀價位:  {TargetPrice[6]:>10.2f}, 潛在漲幅: {Profit[6]:>10.2f}%
"""
        AnueDatas = StockData["Anue"]
        if AnueDatas["EPS(EST)"]:
            TargetPrice = AnueDatas["Factest目標價"]
            Profit = getProfit(TargetPrice, ClossPrice)
            text += f"""
============================================================================
Factest預估

估計EPS: {AnueDatas["EPS(EST)"]:>10.2f}  預估本益比：    {AnueDatas["PE(EST)"]:>10.2f}
Factest目標價: {TargetPrice:>10.2f}  推算潛在漲幅為:  {Profit:>10.2f}
資料日期: {AnueDatas["資料時間"]}  
url: {AnueDatas["ANUEurl"]}
"""
        else:
            pass

        rate = StockData["ESTPER"]
        TargetPrice = [getTarget(rate[i], eps) for i in range(4)]
        Profit = [getProfit(TargetPrice[i], ClossPrice) for i in range(4)]
        text += f"""
============================================================================
本益比四分位數與平均本益比......

PE 25% : {rate[0]:>10.2f}          目標價位: {TargetPrice[0]:>10.2f}          潛在漲幅: {Profit[0]:>10.2f}%
PE 50% : {rate[1]:>10.2f}          目標價位: {TargetPrice[1]:>10.2f}          潛在漲幅: {Profit[1]:>10.2f}%
PE 75% : {rate[2]:>10.2f}          目標價位: {TargetPrice[2]:>10.2f}          潛在漲幅: {Profit[2]:>10.2f}%
PE平均% : {rate[3]:>10.2f}          目標價位: {TargetPrice[3]:>10.2f}          潛在漲幅: {Profit[3]:>10.2f}%
"""

        rate = StockData["SDESTPER"]
        TargetPrice = [getTarget(rate[i], eps) for i in range(7)]
        Profit = [getProfit(TargetPrice[i], ClossPrice) for i in range(7)]
        text += f"""
============================================================================
本益比標準差......

PE TL+3SD: {rate[0]:>10.2f}          目標價位: {TargetPrice[0]:>10.2f}          潛在漲幅: {Profit[0]:>10.2f}%
PE TL+2SD: {rate[1]:>10.2f}          目標價位: {TargetPrice[1]:>10.2f}          潛在漲幅: {Profit[1]:>10.2f}%
PE TL+1SD: {rate[2]:>10.2f}          目標價位: {TargetPrice[2]:>10.2f}          潛在漲幅: {Profit[2]:>10.2f}%
PE TLSD  : {rate[3]:>10.2f}          目標價位: {TargetPrice[3]:>10.2f}          潛在漲幅: {Profit[3]:>10.2f}%
PE TL-1SD: {rate[4]:>10.2f}          目標價位: {TargetPrice[4]:>10.2f}          潛在漲幅: {Profit[4]:>10.2f}%
PE TL-2SD: {rate[5]:>10.2f}          目標價位: {TargetPrice[5]:>10.2f}          潛在漲幅: {Profit[5]:>10.2f}%
PE TL-3SD: {rate[6]:>10.2f}          目標價位: {TargetPrice[6]:>10.2f}          潛在漲幅: {Profit[6]:>10.2f}%
"""

        rate = StockData["ESTPBR"]
        TargetPrice = [getTarget(rate[i], bps) for i in range(4)]
        Profit = [getProfit(TargetPrice[i], ClossPrice) for i in range(4)]
        text += f"""
============================================================================
股價淨值比四分位數與平均本益比......

PB 25% : {StockData["ESTPBR"][0]:>10.2f}           目標價位: {TargetPrice[0]:>10.2f}          潛在漲幅: {Profit[0]:>10.2f}%
PB 50% : {StockData["ESTPBR"][1]:>10.2f}           目標價位: {TargetPrice[1]:>10.2f}          潛在漲幅: {Profit[1]:>10.2f}%
PB 75% : {StockData["ESTPBR"][2]:>10.2f}           目標價位: {TargetPrice[2]:>10.2f}          潛在漲幅: {Profit[2]:>10.2f}%
PB 平均 : {StockData["ESTPBR"][3]:>10.2f}           目標價位: {TargetPrice[3]:>10.2f}          潛在漲幅: {Profit[3]:>10.2f}%
"""

        rate = StockData["SDESTPBR"]
        TargetPrice = [getTarget(rate[i], bps) for i in range(7)]
        Profit = [getProfit(TargetPrice[i], ClossPrice) for i in range(7)]
        text += f"""
============================================================================
股價淨值比標準差......

PB TL+3SD : {rate[0]:>10.2f}           目標價位: {TargetPrice[0]:>10.2f}          潛在漲幅: {Profit[0]:>10.2f}%
PB TL+2SD : {rate[1]:>10.2f}           目標價位: {TargetPrice[1]:>10.2f}          潛在漲幅: {Profit[1]:>10.2f}%
PB TL+1SD : {rate[2]:>10.2f}           目標價位: {TargetPrice[2]:>10.2f}          潛在漲幅: {Profit[2]:>10.2f}%
PB TLSD   : {rate[3]:>10.2f}           目標價位: {TargetPrice[3]:>10.2f}          潛在漲幅: {Profit[3]:>10.2f}%
PB TL-1SD : {rate[4]:>10.2f}           目標價位: {TargetPrice[4]:>10.2f}          潛在漲幅: {Profit[4]:>10.2f}%
PB TL-2SD : {rate[5]:>10.2f}           目標價位: {TargetPrice[5]:>10.2f}          潛在漲幅: {Profit[5]:>10.2f}%
PB TL-3SD : {rate[6]:>10.2f}           目標價位: {TargetPrice[6]:>10.2f}          潛在漲幅: {Profit[6]:>10.2f}%
"""

        peg = StockData["PEG"]
        if peg or eps != StockData["EPS(TTM)"]:
            if eps != StockData["EPS(TTM)"]:
                epsGrowth = (eps / StockData["EPS(TTM)"] - 1) * 100
                peg = StockData["PE(TTM)"] / epsGrowth
                TargetPrice = getTarget(epsGrowth, StockData["EPS(TTM)"])
            else:
                epsGrowth = getTarget(1 / peg, StockData["EPS(TTM)"])
                TargetPrice = ClossPrice / peg
            Profit = getProfit(TargetPrice, ClossPrice)
            text += f"""
============================================================================
PEG估值......

PEG: {peg:>10.2f}           EPS成長率: {epsGrowth :>10.2f}
目標價位: {TargetPrice:>10.2f}          潛在漲幅: {Profit:>10.2f}%
"""
        else:
            pass

    write2txt(text, fw)


def ResultOutput(result_path, StockDatas, EPSLists=None):
    csvOutput(result_path, StockDatas)
    txtOutput(result_path, StockDatas, EPSLists)

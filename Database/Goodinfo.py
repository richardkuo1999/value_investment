import os
import sys
import aiohttp
import asyncio
import logging

sys.path.append(os.path.dirname(__file__) + "/..")
from utils.utils import fetch_webpage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GOODINFO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
    "Cookie": "CLIENT%5FID=20241210210956023%5F111%2E255%2E220%2E131; IS_TOUCH_DEVICE=F; SCREEN_SIZE=WIDTH=1710&HEIGHT=1112; TW_STOCK_BROWSE_LIST=2330; _ga=GA1.1.812880287.1733836199; _cc_id=28e3f970dec12837e20c15307c56ec28; panoramaId_expiry=1734441000958; panoramaId=cc21caa7184af9f0e6c620d0a8f8185ca02cc713f5ac9a4263f82337f1b4a2b7; panoramaIdType=panoDevice; __gads=ID=b2e3ed3af73d1ae3:T=1733836201:RT=1733922308:S=ALNI_Mb7ThRkzKYSy21PA-6lcXT9vRc3Kg; __gpi=UID=00000f896331f355:T=1733836201:RT=1733922308:S=ALNI_MZqCnVGqHlRq9KdKeQAuDHF4Gjfxw; __eoi=ID=f9846d25b9e203d1:T=1733836201:RT=1733922308:S=AA-AfjY-BVqunx2hOWeWbgCq5_UI; cto_bundle=Lk53dF84ZDdteU1aenVEZW9WZklPTG5FYU9MdDRjOFQ5NkVoZ1lYOTVnMzNVTFFDOUFNYXZyWjBmSndHemVhOFdhQTlMZHJUNCUyQiUyRm9RSlJpd0FBUXlYd2NDQmdXRkh0ZkM1SUY1VHM2b2NQc0ljcVJGSTFwY3RPRmI1WEwxRXBMTVUzUDgxWjBLSUVjOSUyQk1veUdMcFZjRDlsNVElM0QlM0Q; cto_bundle=4XBCG184ZDdteU1aenVEZW9WZklPTG5FYU9NcXlSZm1lU2RKOGgwaHlUM1RzWXU5QWMlMkJuR1lkb25qSjdRYUxHWWhsUEhMRGxCeHVuUVF6WGlGTkxjbVNuYmFqbERVRm11QjlTR0xBckVvdmE2ZlJFQmhQdURma3lnRHNjM25xOFpNNEg4WWZLc0wxZVN6c1lEUFZDM3VvNnlxdWFGV2FiNThNRSUyRlZ4N3ZxakZzT3I0cEclMkZYdm1NN2RQNSUyRlBUM1FQJTJCSE80YUxVVDlKUUFLblZuMllUZVBzaVdFZyUzRCUzRA; cto_bidid=NK15uF9ZWnQ2aGIwVGNqRUFJRGgxVUVSejh0b1dEczFNU0FJTmR1RVl5SnljdDVmY08xc1NndnRUZXZMYmVvJTJCMVNya2R5RVk1QWpEeiUyQnBsJTJCOUZJQTBWJTJGcGhTcWFvUGs1QkxuUCUyQnVjUU42MXZIQWxSb2xsVVFrNml2T2g0TG1NcHphS0I4YzdzQXVRVXpRSXlCZU1VV1M4SDN3JTNEJTNE; FCNEC=%5B%5B%22AKsRol-AsNGK3J633zneXVvjb6XxOsqQYrBvxCwcMi0GME-2BDMLBX3LEYQ83Li8Hw71LSdsgNxpfHUX3Nw3FGDMDQhm3wUeXgalEarK4zql1IO51tBobJmU-o44Bd5tOC0OcT6RNUf2w8Bl6YsQ6f2yA7JoK-Uwlw%3D%3D%22%5D%5D; _ga_0LP5MLQS7E=GS1.1.1733921765.2.1.1733922576.51.0.0",
}


TRADING_DATA_BASE_URL = "https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID={}"
COMPANY_INFO_BASE_URL = "https://goodinfo.tw/tw/BasicInfo.asp?STOCK_ID={}"


class Goodinfo:
    async def fetch_data(self, session, stock_id: str):
        tasks = [
            self.get_trading_data(session, stock_id),
            self.get_company_info(session, stock_id)
        ]
        trading_data, company_info = await asyncio.gather(*tasks, return_exceptions=True)
        return {"trading_data": trading_data, "company_info": company_info}

    async def get_trading_data(self, session, stock_id):
        url = TRADING_DATA_BASE_URL.format(stock_id)
        try:
            soup = await fetch_webpage(session, url, headers=GOODINFO_HEADERS)

            table = soup.find("table", class_=lambda x: x and "b0v1h0" in x)
            if not table:
                logger.warning(f"No trading data table found for stock {stock_id}")
                return None

            stock_data = table.find_all("tr")
            if not stock_data:
                logger.warning(f"No stock data rows found for stock {stock_id}")
                return None

            return self.__process_stock_trading_info(stock_data)
        except Exception as e:
            logger.error(
                f"Failed to retrieve trading data for stock {stock_id}: {e}"
            )
            return None

    async def get_company_info(self, session, stock_id):
        url = COMPANY_INFO_BASE_URL.format(stock_id)
        try:
            soup = await fetch_webpage(session, url, GOODINFO_HEADERS)
            info_dict = {}
            keys = soup.find_all("th", {"class": "bg_h1"}, "nobr")
            values = soup.find_all("td", {"bgcolor": "white"}, "p")
            for k, v in zip(keys, values):
                info_dict[k.text.strip()] = v.text.strip()

            return info_dict
        except Exception as e:
            logger.error(
                f"Failed to retrieve company info for stock {stock_id}: {e}"
            )
            return None

    def __process_stock_trading_info(self, tr_elements):
        trading_info = {}
        current_headers = []

        for tr in tr_elements:
            try:
                # Handle header row (stock ID, name, and date)
                if tr.get("class") == ["bg_h0"] and tr.find("th", {"colspan": "8"}):
                    stock_info = tr.find("h2").get_text(strip=True)
                    stock_id, stock_name = stock_info.split("\xa0")
                    trading_info["股票代號"] = stock_id
                    trading_info["股票名稱"] = stock_name
                    data_date = tr.find("nobr", string=lambda x: x and "資料日期" in x)
                    if data_date:
                        trading_info["資料日期"] = data_date.get_text(strip=True).split(": ")[1]
                    continue

                # Capture headers (bg_h1 rows)
                if tr.get("class") == ["bg_h1"] and not tr.find("td", {"colspan": "8"}):
                    current_headers = [
                        th.get_text(strip=True) for th in tr.find_all("th")]
                    continue

                # Process data rows (bgcolor="white")
                if tr.get("bgcolor") == "white" and current_headers:
                    cells = tr.find_all("td")
                    if len(cells) <= len(current_headers):
                        for header, cell in zip(current_headers, cells):
                            key = header
                            value = cell.get_text(strip=True)
                            if cell.get("colspan") == "3":
                                value = value.split("\xa0")[0]  # Extract primary value
                            if key and value:
                                trading_info[key] = value
                    else:
                        logger.warning("Mismatched headers and cells in row: {}"
                                       .format(tr.get_text(strip=True))
                        )

                # Process summary row (連漲連跌, 財報評分, 上市指數)
                if tr.get("class") == ["bg_h1"] and tr.find("td", {"colspan": "8"}):
                    summary_text = tr.find("td").get_text(strip=True, separator=" ")
                    try:
                        # Extract 連漲連跌
                        if "連漲連跌" in summary_text:
                            trend = (
                                summary_text.split("連漲連跌:")[1]
                                .split("財報評分")[0]
                                .strip()
                            )
                            trading_info["連漲連跌"] = trend.replace("\xa0", " ")

                        # Extract 財報評分
                        if "財報評分" in summary_text:
                            score_part = (
                                summary_text.split("財報評分:")[1]
                                .split("上市指數")[0]
                                .strip()
                            )
                            score_parts = score_part.split("/")
                            if len(score_parts) >= 2:
                                trading_info["財報評分_最新"] = (
                                    score_parts[0].strip().removeprefix("最新")
                                )
                                trading_info["財報評分_平均"] = (
                                    score_parts[1].strip().removeprefix("平均")
                                )
                            else:
                                logger.warning(f"Invalid 財報評分 format: {score_part}")
                                trading_info["財報評分_最新"] = (
                                    score_parts[0].strip().removeprefix("最新")
                                )
                                trading_info["財報評分_平均"] = ""

                        # Extract 上市指數
                        if "上市指數" in summary_text:
                            index = summary_text.split("上市指數 :")[1].strip()
                            trading_info["上市指數"] = index.replace("\xa0", " ")
                    except Exception as e:
                        logger.error(f"Error parsing summary row: {summary_text}: {e}")
                        continue

            except Exception as e:
                logger.error(f"Error processing row {tr.get_text(strip=True)}: {e}")
                continue

        return trading_info


async def main():
    stock_id = "2330"  # Example stock ID
    goodinfo = Goodinfo()
    async with aiohttp.ClientSession() as session:
        goodinfo_data = await goodinfo.fetch_data(session, stock_id)
    logger.info(f"trading_data: {goodinfo_data['trading_data']}")
    logger.info(f"company_info: {goodinfo_data['company_info']}")


if __name__ == "__main__":
    asyncio.run(main())

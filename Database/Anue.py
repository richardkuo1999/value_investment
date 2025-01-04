from datetime import datetime
from googlesearch import search
from urllib.parse import unquote

from utils.utils import fetch_webpage


class ANUE:
    def __init__(self, stock_id, stock_name, CatchURL, level):
        self.stock_id = stock_id
        self.stock_name = stock_name
        self.CatchURL = CatchURL
        self.level = level
        self.FactsetData = self.crwal_estimate_eps()

    def crwal_estimate_eps(self):
        stock_id = self.stock_id
        CatchURL = self.CatchURL
        level = self.level
        estprice = None
        EPS = None
        DataTime = datetime(1970, 1, 1, 0, 0, 0)
        url = None
        tm_yday = float(datetime.now().timetuple().tm_yday)

        # Get the cnyes news
        url_list = self.get_search_results(10)
        # print(url_list)

        urldata = []
        for url in url_list:
            try:
                soup = fetch_webpage(url)
                webtime = soup.find(class_="alr4vq1").contents[-1]
                webtime = datetime.strptime(webtime, "%Y-%m-%d %H:%M")
                urldata.append({"date": webtime, "url": url})
                # print(webtime, url)
            except:
                continue

        if (
            stock_id in CatchURL
            and isinstance(CatchURL[stock_id]["url"], str)
            and CatchURL[stock_id]["url"] not in url_list
        ):
            urldata.append(
                {
                    "date": CatchURL[stock_id]["DataTime"],
                    "url": CatchURL[stock_id]["url"],
                }
            )

        sorted_data = sorted(urldata, key=lambda x: x["date"], reverse=True)
        # print(sorted_data)
        for i, timeurl in enumerate(sorted_data):
            try:
                DataTime, url = timeurl["date"], timeurl["url"]
                print(DataTime, ":", url)
                soup = fetch_webpage(url)
                webtitle = soup.find(id="article-container").text

                if webtitle.split("(")[1].split("-")[0] != str(stock_id):
                    continue

                try:
                    estprice = webtitle.split("預估目標價為")[1].split("元")[0]
                except:
                    pass

                rows = soup.table.find_all("tr")  # 提取表格的行
                headers = [
                    header.get_text(strip=True) for header in rows[0].find_all("td")
                ]  # 提取表頭
                EPSeveryear = [headers]

                # print(headers[0])
                if headers[0] != "預估值":
                    continue

                # 提取每行數據並加入結果列表
                for row in rows[1:]:
                    cells = row.find_all("td")
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    EPSeveryear.append(row_data)

                for idx, s in enumerate(headers):
                    if str(datetime.now().year) in s:
                        ThisYearEPSest = float(EPSeveryear[level][idx].split("(")[0])
                        if idx < len(headers) - 1:
                            NextYearEPSest = float(
                                EPSeveryear[level][idx + 1].split("(")[0]
                            )
                            EPS = (((366 - tm_yday) / 366) * ThisYearEPSest) + (
                                (tm_yday / 366) * NextYearEPSest
                            )
                        else:
                            EPS = ThisYearEPSest
                        print("\n", stock_id, " ", EPS, ":", DataTime, ":", url)
                        return (float(estprice), EPS, DataTime, url)
            except Exception as e:
                print(f"Error processing data: {e}, {url}")
                DataTime = datetime(1970, 1, 1, 0, 0, 0)
        return estprice, EPS, DataTime, url

    def get_search_results(self, num_results=10):
        # Get the cnyes news
        # search_str = f'factset eps cnyes {self.stock_id} tw site:news.cnyes.com AND intitle:"{self.stock_id}" AND intitle:"factset"'
        # search_str = f'"鉅亨速報 - Factset 最新調查："{self.stock_name}({self.stock_id}-TW)"EPS預估" site:news.cnyes.com'
        search_str = f"鉅亨速報 - Factset 最新調查：{self.stock_name}({self.stock_id}-TW)EPS預估+site:news.cnyes.com"
        # print(search_str)

        search_results = []
        # url = f"https://www.google.com/search?q={query}&num={num_results}"
        url = f"https://tw.search.yahoo.com/search?p={search_str}&fr=yfp-search-sb"
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
        # print(search_results)

        return [j.replace("print", "id") for j in search_results if "cnyes.com" in j]

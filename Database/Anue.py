import os
import sys
import logging
from datetime import datetime
from urllib.parse import unquote

sys.path.append(os.path.dirname(__file__) + "/..")
from utils.utils import fetch_webpage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ANUE:
    def __init__(self, stock_id: str, stock_name: str, catch_url: dict, level: int):
        self.stock_id = stock_id
        self.stock_name = stock_name
        self.catch_url = catch_url
        self.level = level
        self.FactsetData = self.crawl_estimate_eps()

    def get_search_results(self, num_results=10) -> list[str]:
        search_str = ("鉅亨速報 - Factset 最新調查：{}({}-TW)EPS預估+site:news.cnyes.com"
                                            .format(self.stock_name, self.stock_id))
        # url = f"https://www.google.com/search?q={query}&num={num_results}"
        url = f"https://tw.search.yahoo.com/search?p={search_str}&fr=yfp-search-sb"

        try:
            soup = fetch_webpage(url)
            left_div = soup.find("div", id="left")
            if not left_div:
                logger.warning(f"No search results found for {self.stock_id}")
                return []

            search_results = []
            for link in left_div.find_all("a"):
                href = link.get("href", "")
                if "https%3a%2f%2fnews.cnyes.com%2fnews%2fid%2f" in href:
                    decoded_url = unquote(href.split("/RK=")[0].split("RU=")[1])
                    if "cnyes.com" in decoded_url:
                        search_results.append(decoded_url.replace("print", "id"))

            return search_results[:num_results]
        except Exception as e:
            logger.error(f"Failed to fetch search results for {self.stock_id}: {e}")
            return []

    def crawl_estimate_eps(self):
        tm_yday = float(datetime.now().timetuple().tm_yday)

        # Retrieve cached data if available
        cached_data = self.catch_url.get(self.stock_id, {})
        cached = (
            cached_data.get("Factest目標價", None),
            cached_data.get("EPS(EST)", None),
            cached_data.get("資料時間", datetime(1970, 1, 1, 0, 0, 0)),
            cached_data.get("ANUEurl", None),
        )

        # Fetch search results
        logger.info(f"Fetching search results for {self.stock_id}")
        url_list = self.get_search_results(10)

        # Collect URLs with their timestamps
        url_data = []
        for url in url_list:
            try:
                soup = fetch_webpage(url)
                webtime_elem = soup.find(class_="alr4vq1")
                if not webtime_elem:
                    continue
                webtime = datetime.strptime(webtime_elem.contents[-1], "%Y-%m-%d %H:%M")
                url_data.append({"date": webtime, "url": url})
            except Exception as e:
                logger.warning(f"Failed to parse date for URL {url}: {e}")
                continue

        # Include cached URL if not in search results
        if cached[3] and cached[3] not in url_list:
            url_data.append({"date": datetime.strptime(cached[2], "%Y/%m/%d"), "url": cached[3]})

        # Sort by date (newest first)
        sorted_data = sorted(url_data, key=lambda x: x["date"], reverse=True)

    # Process each URL
        for time_url in sorted_data:
            try:
                data_time, url = time_url["date"], time_url["url"]
                soup = fetch_webpage(url)
                article = soup.find(id="article-container")
                if not article:
                    continue

                webtitle = article.text
                title_stock_id = webtitle.split("(")[1].split("-")[0]
                if title_stock_id != str(self.stock_id):
                    continue

                # Extract estimated target price
                try:
                    est_price = float(webtitle.split("預估目標價為")[1].split("元")[0])
                except (IndexError, ValueError):
                    continue

                # Extract EPS data from table
                table = soup.find("table")
                if not table:
                    continue

                rows = table.find_all("tr")
                headers = [header.get_text(strip=True) for header in rows[0].find_all("td")]
                if headers[0] != "預估值":
                    continue

                eps_data = [[cell.get_text(strip=True) for cell in row.find_all("td")] for row in rows[1:]]
                eps_data.insert(0, headers)

                # Calculate weighted EPS
                current_year = str(datetime.now().year)
                for idx, header in enumerate(headers):
                    if current_year in header:
                        this_year_eps = float(eps_data[self.level][idx].split("(")[0])
                        next_year_eps = (
                            float(eps_data[self.level][idx + 1].split("(")[0])
                            if idx < len(headers) - 1
                            else this_year_eps
                        )
                        weighted_eps = (
                            ((366 - tm_yday) / 366) * this_year_eps +
                            (tm_yday / 366) * next_year_eps
                        )
                        logger.info("{} EPS: {}, Date: {}, URL: {}"
                                    .format(self.stock_id, weighted_eps, data_time, url))
                        return (est_price, weighted_eps, data_time, url)
            except Exception as e:
                logger.warning(f"Error processing URL {url}: {e}")
                continue

        logger.warning("No valid EPS data found for {}, returning cached/default data"
                       .format(self.stock_id))
        return cached
    
if __name__ == "__main__":
    # Example usage
    stock_id = "2330"
    stock_name = "台積電"
    catch_url = {
        stock_id: {
            "Factest目標價": 600,
            "EPS(EST)": 20,
            "資料時間": datetime(2023, 1, 1),
            "ANUEurl": "https://example.com",
        }
    }
    level = 4

    anue = ANUE(stock_id, stock_name, catch_url, level)
    print(anue.FactsetData)
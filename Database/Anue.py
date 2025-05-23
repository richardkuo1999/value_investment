import os
import sys
import aiohttp
import asyncio
from datetime import datetime
from urllib.parse import unquote

sys.path.append(os.path.dirname(__file__) + "/..")
from utils.utils import logger, fetch_webpage


GOOGLE_SEARCH_BASE_URL = "https://www.google.com/search?q={}&num={}"
YAHOO_SEARCH_BASE_URL = "https://tw.search.yahoo.com/search?p={}&fr=yfp-search-sb"
CNYEA_URL = "https%3a%2f%2fnews.cnyes.com%2fnews%2fid%2f"


class ANUE:
    def __init__(self, catch_url: dict, level: int):
        self.catch_url = catch_url
        self.level = level

    async def fetch_data(self, session, stock_id, stock_name):
        return await self.__crawl_estimate_eps(session, stock_id, stock_name)

    async def __search_results(self, session, stock_id, stock_name, num_results=10) -> list[str]:
        search_str = (
            "鉅亨速報 - Factset 最新調查：{}({}-TW)EPS預估+site:news.cnyes.com".format(
                stock_name, stock_id
            )
        )

        # url = GOOGLE_SEARCH_BASE_URL.format(search_str, num_results)
        url = YAHOO_SEARCH_BASE_URL.format(search_str)

        try:
            soup = await fetch_webpage(session, url)
            left_div = soup.find("div", id="left")
            if not left_div:
                logger.warning(f"No search results found for {stock_id}")
                return []

            search_results = []
            for link in left_div.find_all("a"):
                href = link.get("href")
                if CNYEA_URL in href:
                    decoded_url = unquote(href.split("/RK=")[0].split("RU=")[1])
                    if "cnyes.com" in decoded_url:
                        search_results.append(decoded_url.replace("print", "id"))

            return search_results[:num_results]
        except Exception as e:
            logger.warning(f"Failed to fetch search results for {stock_id}: {e}")
            return []

    async def __process_page(self, session, stock_id, url_list, tm_yday, cached):
        async def __process_single_page(session, url, stock_id):
            try:
                soup = await fetch_webpage(session, url)
                if not soup:
                    logger.debug("soup is empty")
                    return None

                webtime_elem = soup.find(class_="alr4vq1")
                if not webtime_elem:
                    logger.debug("webtime_elem is empty")
                    return None

                data_time = datetime.strptime(
                    webtime_elem.contents[-1].text, "%Y-%m-%d %H:%M"
                )
                if not data_time:
                    logger.debug("data_time is empty")
                    return None

                article = soup.find(id="article-container")
                if not article:
                    logger.debug("article is empty")
                    return None

                webtitle = article.text
                title_stock_id = webtitle.split("(")[1].split("-")[0]
                if title_stock_id != str(stock_id):
                    logger.debug(f"title_stock_id is {title_stock_id} not {stock_id}")
                    return None

                # Extract estimated target price
                try:
                    est_price = float(webtitle.split("預估目標價為")[1].split("元")[0])
                except (IndexError, ValueError):
                    logger.debug(f"Didn't have estimated target pric")
                    return None

                # Extract EPS data from table
                table = soup.find("table")
                if not table:
                    logger.debug(f"Didn't have EPS data")
                    return None

                rows = table.find_all("tr")
                headers = [
                    header.get_text(strip=True) for header in rows[0].find_all("td")
                ]
                if not headers or headers[0] != "預估值":
                    logger.debug(f"headers didn't find the 預估值")
                    return None

                eps_data = [
                    [cell.get_text(strip=True) for cell in row.find_all("td")]
                    for row in rows[1:]
                ]
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
                        weighted_eps = ((366 - tm_yday) / 366) * this_year_eps + (
                            tm_yday / 366
                        ) * next_year_eps
                        logger.debug(
                            f"{stock_id} EPS: {weighted_eps}, Date: {data_time}, URL: {url}"
                        )
                        return (est_price, weighted_eps, data_time, url)
                return None
            except Exception as e:
                logger.warning(f"Error processing URL {url}: {e}")
                return None

        tasks = [__process_single_page(session, url, stock_id) for url in url_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Find the first valid result
        valid_results = [x for x in results if x is not None]
        if valid_results:
            sorted_data = sorted(valid_results, key=lambda x: x[2], reverse=True)
            last_result = sorted_data[0]
            logger.info(last_result)
            return last_result

        logger.warning(
            f"No valid EPS data found for {stock_id}, returning cached/default data"
        )
        return cached

    async def __crawl_estimate_eps(self, session, stock_id, stock_name):
        tm_yday = float(datetime.now().timetuple().tm_yday)

        # Retrieve cached data if available
        cached_data = self.catch_url.get(stock_id, {})
        cached = (
            cached_data.get("Factest目標價", None),
            cached_data.get("EPS(EST)", None),
            cached_data.get("資料時間", datetime(1970, 1, 1, 0, 0, 0)),
            cached_data.get("ANUEurl", None),
        )

        # Fetch search results
        logger.debug(f"Fetching search results for {stock_id}")
        url_list = await self.__search_results(session, stock_id, stock_name, 10)
        if cached[3] and cached[3] not in url_list:
            url_list.append(cached[3])

        # Process each URL
        return await self.__process_page(session, stock_id, url_list, tm_yday, cached)


async def main():
    stock_id = "2330"
    stock_name = "台積電"
    catch_url = {
        stock_id: {
            "Factest目標價": 600,
            "EPS(EST)": 20,
            "資料時間": "2023/1/1",
            "ANUEurl": "https://example.com",
        }
    }
    level = 4

    anue = ANUE(catch_url, level)
    async with aiohttp.ClientSession() as session:
        anue_data = await anue.fetch_data(session, stock_id, stock_name)
    logger.info(anue_data)


if __name__ == "__main__":
    asyncio.run(main())

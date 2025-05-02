import aiohttp
import asyncio
from bs4 import BeautifulSoup
from groq import Groq
from datetime import datetime
import yaml, html, re, logging
import feedparser

# Groq API Key
GROQ_API_KEY = yaml.safe_load(open('token.yaml'))["GROQ_API_KEY"][0]

class AsyncNewsParser:
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.groq = Groq(api_key=GROQ_API_KEY)
        self.model = "llama3-70b-8192"
        self.logger.info(f"model = {self.model}")

        # Mapping sites to parser functions
        self.parser_dict = {
            'udn': self.udn_news_parser,
            'cnyes': self.cnyes_news_parser,
            'moneydj': self.moneyDJ_news_parser
        }
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        self.session = None
        self.logger.info("AsyncNewsParser init done")

    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        self.logger.info("AsyncNewsParser init session done")

    async def close(self):
        await self.session.close()

    def clean_all(self, text):
        # 1. 解碼 HTML Entities，如 &nbsp; &lt;
        text = html.unescape(text)
        # 2. 移除 HTML 標籤，如 <div>、<a href=...>等
        text = re.sub(r"<[^>]+>", "", text)
        return text

    async def rss_parser(self, url: str) -> list[dict] | None:
        results = None
        try:
            async with self.session.get(url) as resp:
                text = await resp.text()
            feed = feedparser.parse(text)
            results = [{'title': entry.title, 'url': entry.link, 'src': 'rss'} for entry in feed.entries]
            self.logger.info("get rss items done")
        except Exception as e:
            self.logger.error(e)
        return results
    
    async def news_request(self, url: str, params: dict | None = None) -> BeautifulSoup | None:
        try:
            async with self.session.get(url, params=params) as resp:
                resp.raise_for_status()
                text = await resp.text()
                return BeautifulSoup(text, 'html.parser')
        except Exception as e:
            self.logger.error(f"HTTP request error: {e}")
            return None
    
    def moneyDJ_news_parser(self, soup) -> str:
        # 解析 MONEYDJ 的新聞
        self.logger.debug("解析 MONEYDJ 的新聞")
        paragraphs = soup.find('article').find_all('p')
        content = "\n".join(p.get_text(strip=True) for p in paragraphs[:-1])
        self.logger.debug(f"📰 新聞內文：{content}\n")
        return content

    def udn_news_parser(self, soup) -> str:
        # 解析 MONEY.UDN 的新聞
        self.logger.debug("解析 MONEY UDN 的新聞")
        paragraphs = soup.find('section', class_="article-body__editor").find_all('p')  # 內文區塊
        content = "\n".join(p.get_text(strip=True) for p in paragraphs[:-1])
        self.logger.debug(f"📰 新聞內文：\n{content}")
        return content

    def cnyes_news_parser(self, soup) -> str:
        # 解析 CNYES 的新聞
        content = soup.find('main', class_='c1tt5pk2').text.strip()
        self.logger.debug(f"📰 新聞內文：\n{content}")
        return content

    async def fetch_news_content(self, url: str) -> str | None:
        soup = await self.news_request(url)
        if soup is None:
            return None
        for key, func in self.parser_dict.items():
            if key in url:
                self.logger.debug(f"Website is {key}")
                return func(soup)
        self.logger.error("Unsupported website")
        return None

    async def fetch_cnyes_newslist(self, url: str, limit: int = 20) -> list[dict]:
        params = {"limit": limit}
        async with self.session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()
        articles = data.get("items", {}).get("data", [])
        result = []
        for article in articles:
            title = article["title"]
            content = self.clean_all(article.get("content", ""))
            pub_time = datetime.fromtimestamp(article.get("publishAt", 0)).strftime("%Y-%m-%d %H:%M")
            news_url = f"https://news.cnyes.com/news/id/{article['newsId']}"
            result.append({
                "title": title,
                "content": content,
                "time": pub_time,
                "url": news_url
            })
        return result

    async def fetch_news_list(self, url: str, news_number: int = 10) -> list[dict]:
        if 'cnyes.com' in url:
            news_result = await self.fetch_cnyes_newslist(url, limit=news_number)
        else:
            news_result = await self.rss_parser(url)

        # Fetch content for crawl sources if needed
        # (Example placeholder; crawl logic can be added similarly)

        return news_result[:news_number]
    
    async def fetch_report(self, url: str, report_number: int = 10) -> list[dict]:
        if 'fugle' in url:
            return await self.get_fugle_report(url)
        result = await self.rss_parser(url)
        return result[:report_number]

    async def get_fugle_report(self, url: str) -> list[dict]:
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            text = await resp.text()
        soup = BeautifulSoup(text, "html.parser")
        articles = soup.select('.col-12')
        reports = []
        for article in articles:
            title = article.select_one(".post-title").get_text(strip=True)
            link = article.select_one('a')['href']
            reports.append({'title': title, 'url': link})
        return reports

    async def get_uanalyze_report(self) -> list[dict]:
        url = 'https://uanalyze.com.tw/articles'
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            text = await resp.text()
        soup = BeautifulSoup(text, "html.parser")
        block = soup.select('.article-list')
        articles = block[0].select(".article-content") if block else []
        reports = []
        for article in articles:
            title = article.select_one(".article-content__title").get_text(strip=True)
            link = article.select_one('a')['href']
            reports.append({'title': title, 'url': link})
        return reports
    
    async def get_vocus_ieobserve_articles(self) -> list[dict]:
        url = "https://vocus.cc/user/@ieobserve"
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            text = await resp.text()
        soup = BeautifulSoup(text, "html.parser")
        link_prefix = 'https://vocus.cc'
        articles = soup.find_all("div", attrs={"class": ["dHnwX", "dDuosN"]})
        reports = []
        for article in articles:
            title = article.select_one('span').get_text(strip=True)
            link = link_prefix + article.select_one('a')['href']
            reports.append({'title': title, 'url': link})
        return reports
            
            
# Example usage
if __name__ == "__main__":
    async def main():
        parser = AsyncNewsParser()
        url = 'https://api.cnyes.com/media/api/v1/newslist/category/headline'
        data = await parser.fetch_news_list(url)
        print(data[0] if data else 'No data')
        await parser.close()

    asyncio.run(main())
    

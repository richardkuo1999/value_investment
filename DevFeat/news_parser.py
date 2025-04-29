import requests
from bs4 import BeautifulSoup
from groq import Groq
from datetime import datetime
import time
import yaml
import feedparser
import html
import re
from utils.Logger import setup_logger
# Groq API Key
GROQ_API_KEY = yaml.safe_load(open('token.yaml'))["GROQ_API_KEY"][0]

class NewsParser:
    def __init__(self):
        self.logger = setup_logger()
        self.groq = Groq(api_key=GROQ_API_KEY)
        self.model = "llama3-70b-8192"
        self.logger.info(f"model = {self.model}")
        # ========================================
        # Create a dictionary to map website to parser function
        self.parser_dict = {'udn' : self.udn_news_parser, 'cnyes' : self.cnyes_news_parser, 'moneydj' : self.moneyDJ_news_parser}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

    def clean_all(self, text):
        # 1. 解碼 HTML Entities，如 &nbsp; &lt;
        text = html.unescape(text)
        # 2. 移除 HTML 標籤，如 <div>、<a href=...>等
        text = re.sub(r"<[^>]+>", "", text)
        return text
    
    def rss_parser(self, url):
        feed = feedparser.parse(url)
        res_list = []
        try:
            for entry in feed.entries:
                # self.logger.debug(f"標題：{entry.title}")
                # self.logger.debug(f"連結：{entry.link}")
                # self.logger.debug(f"發布時間：{entry.published}")
                # self.logger.debug("-----------------")
                res_list.append({'title' : entry.title, 'url' : entry.link, "src" : "rss"})
        except Exception as e:
            self.logger.error(e)
            
        return res_list

    def is_supported_website(self, url):
        # 檢查網站是否支援
        return any(site in url for site in self.parser_dict.keys())
    
    def news_request(self, url, params=None):
        """
        Sends an HTTP GET request to the specified URL and parses the response using BeautifulSoup.

        Args:
            url (str): The URL to send the HTTP GET request to.

        Returns:
            BeautifulSoup: A BeautifulSoup object containing the parsed HTML content of the response
                           if the request is successful.
            none: any exception
        """
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()  # 檢查 HTTP 請求是否成功
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
        except Exception as e:
            self.logger.error(f"HTTP 請求錯誤: {e}")
            return None
    
    def moneyDJ_news_parser(self, soup):
        # 解析 MONEYDJ 的新聞
        self.logger.debug("解析 MONEYDJ 的新聞")
        paragraphs = soup.find('article').find_all('p')
        content = "\n".join(p.get_text(strip=True) for p in paragraphs[:-1])
        self.logger.debug(f"📰 新聞內文：{content}\n")
        return content

    def udn_news_parser(self, soup):
        # 解析 MONEY.UDN 的新聞
        self.logger.debug("解析 MONEY UDN 的新聞")
        paragraphs = soup.find('section', class_="article-body__editor").find_all('p')  # 內文區塊
        content = "\n".join(p.get_text(strip=True) for p in paragraphs[:-1])
        self.logger.debug(f"📰 新聞內文：\n{content}")
        return content

    def cnyes_news_parser(self, soup):
        # 解析 CNYES 的新聞
        content = soup.find('main', class_='c1tt5pk2').text.strip()
        self.logger.debug(f"📰 新聞內文：\n{content}")
        return content

    def fetch_news_content(self, url):
        # 根據網址解析新聞內容
        soup = self.news_request(url)
        if isinstance(soup, dict) and "error" in soup:
            self.logger.error(soup["error"])
            return
        
        # 判斷網址屬於哪個網站
        for key, func in self.parser_dict.items():
            if key in url:
                self.logger.debug(f"website is {key}")
                return func(soup)
        
        self.logger.error("不支援的網站")
        return None
    
    def fetch_cynes_newslist(self, url):
        headers = {"User-Agent": "Mozilla/5.0"}
        params = {"limit": 20}
        response = requests.get(url, params, headers=headers)
        response.raise_for_status()
        data = response.json()

        result = []
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()

        data = response.json()
        articles = data["items"]["data"]

        
        for article in articles:
            title = article["title"]
            content = self.clean_all(article["content"])
            pub_time = datetime.fromtimestamp(article["publishAt"]).strftime("%Y-%m-%d %H:%M")
            news_url = f"https://news.cnyes.com/news/id/{article['newsId']}"
            result.append({
                "title": title,
                "content": content,
                "time": pub_time,
                "url": news_url
            })
        return result

    def fetch_news_list(self, url, news_number=10):
        """
        Fetches and processes a list of news articles from a specified website.
        Args:
            website (str): The name of the website to fetch news from. Currently supports "udn".
            url (str, optional): The specific URL to fetch news from. If not provided, the default URL 
                                 associated with the website will be used.
        Returns:
            dict: A dictionary containing an error message if the website is not supported or if there 
                  is an issue with the request.
            None: If the news fetching and processing are successful, the function does not return 
                  anything but prints the news titles, links, and AI-generated summaries.
        """
        news_result = []
        
        
        # if "udn" in url:
        if False:
            soup = self.news_request(url)
            if soup is None: # check return data before use
                return []
            
            news_items = soup.select(".story-headline-wrapper")
            for idx, item in enumerate(news_items[:news_number]):
                # Get the news information
                try:
                    title_tag = item.select_one("a")
                    title = title_tag.get('title').strip()
                    link = title_tag.get("href")
                    content = self.fetch_news_content(link)
                    self.logger.debug(f"\n📌 {title}\n🔗 {link}\n")
                    news_result.append({'title' : title, 'content' : content, 'url' : link, "src" : "crawl"})
                except Exception as e:
                    self.logger.error(e)
        elif "cnyes.com" in url:
            news_result = self.fetch_cynes_newslist(url)
        else:
            news_result = self.rss_parser(url)
        
        return news_result[:news_number] # Get latest 10 news
    
    def fetch_report(self, url, news_number=10):
        data = None
        if 'fugle' in url:
            data = self.get_fugle_report(url)
        else:
            data = self.rss_parser(url)

        return data[:news_number]

    def get_fugle_report(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.select('.col-12')
        reports = []

        for article in articles:
            title = article.select_one(".post-title").get_text(strip=True)
            link = article.select_one("a")["href"]
            reports.append({'title' : title, "url" : link})

        return reports

    def get_uanalyze_report(self):
        url = 'https://uanalyze.com.tw/articles'
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # 找出所有文章區塊
        block = soup.select('.article-list')
        articles = block[0].select(".article-content")
        reports = []
        for article in articles:
            title = article.select_one(".article-content__title").get_text(strip=True)
            link = article.select_one("a")["href"]
            reports.append({'title' : title, "url" : link})

        return reports
    
    def get_vocus_ieobserve_articles(self):
        url = "https://vocus.cc/user/@ieobserve"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        }

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        link_prefix = 'https://vocus.cc'
        articles = soup.find_all("div", attrs={"class": ["dHnwX", "dDuosN"]})
        reports = []
        for article in articles:
            title = article.select_one('span').get_text(strip=True)
            link = link_prefix + article.select_one('a')['href']
            reports.append({'title' : title, "link" : link})

        return reports
            
            

if __name__ == "__main__":
    # Example usage
    # url = 'https://news.cnyes.com/news/id/5930210'
    # url = 'https://udn.com/news/story/7240/8669458'
    # url = 'https://udn.com/news/story/7240/8670516?from=udn-catebreaknews_ch2'
    # fetch_news_content(url)
    url = 'https://udn.com/news/breaknews/1/5#breaknews'
    url = 'https://api.cnyes.com/media/api/v1/newslist/category/headline'
    # fetch_news_list(url, "udn")
    NP = NewsParser()
    url = 'https://morss.it/:proxy/https://www.macromicro.me/blog'
    data = NP.rss_parser(url)
    print(data[0])
    
    # feed = feedparser.parse(url)
    # for entry in feed.entries:
    #     print(entry.published)
    #     break
    

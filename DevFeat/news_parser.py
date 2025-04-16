import requests
from bs4 import BeautifulSoup
from groq import Groq
import time
import yaml
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

    def is_supported_website(self, url):
        # 檢查網站是否支援
        return any(site in url for site in self.parser_dict.keys())
    
    def news_request(self, url):
        """
        Sends an HTTP GET request to the specified URL and parses the response using BeautifulSoup.

        Args:
            url (str): The URL to send the HTTP GET request to.

        Returns:
            BeautifulSoup: A BeautifulSoup object containing the parsed HTML content of the response
                           if the request is successful.
            dict: A dictionary with an error message if the request fails or if parsing encounters an issue.

        Raises:
            None: Exceptions are caught and handled within the method.
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()  # 檢查 HTTP 請求是否成功
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP 請求錯誤: {e}")
            return {"error": "HTTP 請求失敗"}
        except AttributeError as e:
            self.logger.error(f"解析錯誤: {e}")
            return {"error": "無法解析標題或內容"}

    
    def groq_summary(self, content):
        condition = "幫我摘要內容成 5 個要點"
        # condition = "500 字以內的摘要"
        # condition = "幫我找出投資機會"
        prompt = "\n" + condition  + "，並且只能用繁體中文回答。\n"
        response = self.groq.chat.completions.create(
            model = self.model,
            messages=[
                {"role": "user", "content": content + prompt},
            ]
        )
        return response
    
    def moneyDJ_news_parser(self, soup):
        # 解析 MONEYDJ 的新聞
        self.logger.info("解析 MONEYDJ 的新聞")
        title = soup.find('h1').get_text(strip=True)
        paragraphs = soup.find('article').find_all('p')
        content = "\n".join(p.get_text(strip=True) for p in paragraphs[:-1])
        self.logger.debug("📌 新聞標題：{title}")
        self.logger.debug("📰 新聞內文：{content}\n")
        return {"title": title, "content": content}

    def udn_news_parser(self, soup):
        # 解析 MONEY.UDN 的新聞
        self.logger.info("解析 MONEY UDN 的新聞")
        title = soup.find('h1').get_text(strip=True)
        paragraphs = soup.find('section', class_="article-body__editor").find_all('p')  # 內文區塊
        content = "\n".join(p.get_text(strip=True) for p in paragraphs[:-1])
        # print("📌 新聞標題：", title)
        # print("📰 新聞內文：\n", content)
        return {"title": title, "content": content}

    def cnyes_news_parser(self, soup):
        # 解析 CNYES 的新聞
        title = soup.find('h1').text.strip()
        content = soup.find('main', class_='c1tt5pk2').text.strip()
        # print("📌 新聞標題：", title)
        # print("📰 新聞內文：\n", content)
        return {"title": title, "content": content}

    def fetch_news_content(self, url):
        # 根據網址解析新聞內容
        soup = self.news_request(url)
        if isinstance(soup, dict) and "error" in soup:
            self.logger.error(soup["error"])
            return
        # 判斷網址屬於哪個網站
        for key, func in self.parser_dict.items():
            if key in url:
                return func(soup)
        
        self.logger.error("不支援的網站")
        return None

    def fetch_news_list(self, url, news_number=1):
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
        # 檢查網站是否支援
        if not self.is_supported_website(url):
            self.logger.error("不支援的網站")
            return {"error": "不支援的網站"}
        
        soup = self.news_request(url)
        news_result = []
        # 如果請求失敗，則返回錯誤訊息
        # 這裡的錯誤訊息是從 news_request 函數返回的
        # 如果請求成功，則繼續處理
        if isinstance(soup, dict) and "error" in soup:
            print(soup["error"])
            return
        # Get all news items for udn
        if "udn" in url:
            news_items = soup.select(".story-headline-wrapper")
            for idx, item in enumerate(news_items[:news_number]):
                # Get the title tag and link
                title_tag = item.select_one("a")
                if title_tag:
                    title = title_tag.get('title').strip()
                    link  = title_tag.get("href")
                    self.logger.info(f"\n📌 {title}\n🔗 {link}\n")
                    # Fetch the news conten
                    try:
                        news_dict = self.fetch_news_content(link)
                        news_dict['url'] = link
                        news_result.append(news_dict)
                    except Exception as e:
                        self.logger.error(e);

                    time.sleep(5)  # 避免過於頻繁的請求
        elif "moneydj" in url:
            news_items = soup.select(".forumgrid")
            for idx, item in enumerate(news_items[:news_number]):
                title_tag = item.select_one("a")
                if title_tag:
                    title = title_tag.get('title').strip()
                    link  = "https://www.moneydj.com" + title_tag.get("href")
                    self.logger.info(f"\n📌 {title}\n🔗 {link}\n")
                    # Fetch the news content
                    try:
                        news_dict = self.fetch_news_content(link)
                        news_dict['url'] = link
                        news_result.append(news_dict)
                    except Exception as e:
                        self.logger.error(e)
                       
                    time.sleep(5)  # 避免過於頻繁的請求
        else:
            print("不支援的網站")
        return news_result

if __name__ == "__main__":
    # Example usage
    # url = 'https://news.cnyes.com/news/id/5930210'
    # url = 'https://udn.com/news/story/7240/8669458'
    # url = 'https://udn.com/news/story/7240/8670516?from=udn-catebreaknews_ch2'
    # fetch_news_content(url)
    url = 'https://udn.com/news/breaknews/1/5#breaknews'
    # fetch_news_list(url, "udn")
    NP = NewsParser(url)
    NP.fetch_news_list('udn')

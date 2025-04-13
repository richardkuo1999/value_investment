import requests
from bs4 import BeautifulSoup
from groq import Groq
import time
import yaml
# Groq API Key
GROQ_API_KEY = yaml.safe_load(open('token.yaml'))["GROQ_API_KEY"][0]

class NewsParser:
    def __init__(self, url):

        self.groq = Groq(api_key=GROQ_API_KEY)
        self.model = "llama3-70b-8192"
        # ========================================
        self.url = url
        self.supported_website = ['udn', 'cnyes']
        # Create a dictionary to map website to parser function
        self.parser_dict = {'udn' : self.udn_news_parser, 'cnyes' : self.cnyes_news_parser}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

    def is_supported_website(self, website):
        # 檢查網站是否支援
        return any(website in site for site in self.supported_website)
    
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
            print(f"HTTP 請求錯誤: {e}")
            return {"error": "HTTP 請求失敗"}
        except AttributeError as e:
            print(f"解析錯誤: {e}")
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

    def udn_news_parser(self, soup):
        # 解析 UDN 的新聞
        print("解析 UDN 的新聞")
        title = soup.find('h1').get_text(strip=True)
        paragraphs = soup.find('section', class_="article-content__editor").find_all('p')  # 內文區塊
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

    def fetch_news_content(self, url=None):
        # 根據網址解析新聞內容
        soup = self.news_request(self.url if url is None else url)
        if isinstance(soup, dict) and "error" in soup:
            print(soup["error"])
            return
        # 判斷網址屬於哪個網站
        for key, func in self.parser_dict.items():
            if key in url:
                return func(soup)
        
        print("不支援的網站")
        return None

    def fetch_news_list(self, website, url=None):
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
        Behavior:
            - Checks if the specified website is supported. If not, prints an error message and returns 
              an error dictionary.
            - Sends a request to fetch the HTML content of the news page.
            - For the "udn" website:
                - Extracts news items from the page.
                - Prints the title and link for each news item.
                - Fetches the content of each news article.
                - Generates and prints an AI-generated summary of the article.
                - Introduces a delay between requests to avoid overloading the server.
            - For unsupported websites, prints an error message.
        Notes:
            - The function relies on helper methods such as `is_supported_website`, `news_request`, 
              `fetch_news_content`, and `groq_summary`.
            - The function includes a delay (`time.sleep(5)`) to prevent sending requests too frequently.
        """
        # 檢查網站是否支援
        if not self.is_supported_website(website):
            print("不支援的網站")
            return {"error": "不支援的網站"}
        
        soup = self.news_request(self.url if url is None else url)

        # 如果請求失敗，則返回錯誤訊息
        # 這裡的錯誤訊息是從 news_request 函數返回的
        # 如果請求成功，則繼續處理
        if isinstance(soup, dict) and "error" in soup:
            print(soup["error"])
            return
        # Get all news items for udn
        if website == "udn":
            news_items = soup.select(".story-list__news")
            for item in news_items:
                # Get the title tag and link
                title_tag = item.select_one("h2 a")
                if title_tag:
                    title = title_tag.text.strip()
                    link = "https://udn.com" + title_tag.get("href")
                    print(f"\n📌 {title}\n🔗 {link}\n")
                    # Fetch the news content
                    news_dict = self.fetch_news_content(link)
                    # Get the summary
                    response = self.groq_summary(news_dict['content'])
                    print("📰 AI摘要：\n", response.choices[0].message.content)

                    time.sleep(5)  # 避免過於頻繁的請求
        else:
            print("不支援的網站")

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
from utils.utils import fetch_webpage
from Database.Goodinfo import Goodinfo, headers
from utils.Logger import setup_logger
class MoneyDJ:
    def __init__(self) -> None:
        self.query_url = f"https://www.moneydj.com/kmdj/search/list.aspx?_Query_="
        self.wiki_url = "&_QueryType_=WK"
        self.prefix_url = "https://www.moneydj.com/kmdj/"
        self.logger = setup_logger()
        self.logger.info("MoneyDJ initialized")

    def get_company_url(self, stock_id) -> str | None:
        """
        Retrieves the company URL for a given stock ID.
        This method uses the Goodinfo class to fetch stock information and constructs
        a query URL to search for the company's webpage. If the company's webpage is 
        found, the method returns the full URL; otherwise, it returns None.
        Args:
            stock_id (str): The stock ID of the company to retrieve the URL for.
        Returns:
            str | None: The full URL of the company's webpage if found, otherwise None.
        Notes:
            - The method fetches the company name from the Goodinfo class.
            - It constructs a query URL using the company name and performs a web 
              scraping operation to locate the company's webpage.
            - If the webpage is found, the URL is prefixed and returned.
            - If the webpage is not found, a message is printed, and None is returned.
        """
        goodinfo = Goodinfo(stock_id)
        company_url = None

        # 取得公司名稱
        company_name = goodinfo.StockInfo['公司名稱']
        
        # 使用公司名稱進行查詢
        url = self.query_url + company_name + self.wiki_url
        self.logger.debug(f"Query URL: {url}")
        soup = fetch_webpage(url, headers)
        section_title = soup.find("td", string=company_name)

        # 取得查詢結果的網址
        if section_title:
            company_url = section_title.select_one('a').get("href")
            company_url = self.prefix_url + company_url[2:]
            self.logger.debug(f"Company URL: {company_url}")
        else:
            self.logger.warning(f"查無『查詢 - 財經百科』區塊: {url}")

        return company_url

    def get_wiki_result(self, stock_id) -> str:

        company_url = self.get_company_url(stock_id)

        # 確保找到正確的元素
        soup = fetch_webpage(company_url, headers)
        data = soup.find('div', class_='UserDefined')
        self.logger.debug(f"data find is {data is not None}")
        # Get clean text from the data
        raw_text = data.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        clean_text = '\n'.join(lines)
        
        return clean_text
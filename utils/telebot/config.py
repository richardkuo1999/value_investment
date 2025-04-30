import yaml

CONFIG = yaml.safe_load(open('token.yaml'))
NEWS_SOURCE_URLS = {
                '[udn] 產業' : 'https://morss.it/:proxy:items=%7C%7C*[class=story__headline]/https://money.udn.com/rank/newest/1001/5591/1', 
                '[udn] 證券' : 'https://morss.it/:proxy:items=%7C%7C*[class=story__headline]/https://money.udn.com/rank/newest/1001/5590/1',
                '[udn] 國際' : 'https://morss.it/:proxy:items=%7C%7C*[class=story__headline]/https://money.udn.com/rank/newest/1001/5588/1',
                '[udn] 兩岸' : 'https://morss.it/:proxy:items=%7C%7C*[class=story__headline]/https://money.udn.com/rank/newest/1001/5589/1',
                '[鉅亨網] 頭條' : 'https://api.cnyes.com/media/api/v1/newslist/category/headline',
                '[鉅亨網] 台股' : 'https://api.cnyes.com/media/api/v1/newslist/category/tw_stock',
                '[鉅亨網] 美股' : 'https://api.cnyes.com/media/api/v1/newslist/category/wd_stock',
                '[鉅亨網] 科技' : 'https://api.cnyes.com/media/api/v1/newslist/category/tech',
                "News Digest AI（中文）" : "https://feed.cqd.tw/ndai",
                '[moneydj] 發燒頭條' : 'https://www.moneydj.com/KMDJ/RssCenter.aspx?svc=NR&fno=1&arg=MB010000',
                'Yahoo TW' : "https://tw.stock.yahoo.com/rss?category=news",
                }
REPORT_URLS = [
            "https://blog.fugle.tw/",
            "https://feed.cqd.tw/vocus/user/ieobserve", # source: https://github.com/CQD/feeder
            "https://feed.cqd.tw/vocus/user/miula",
            "https://feed.cqd.tw/vocus/user/65ab564cfd897800018a88cc",
            "https://morss.it/:proxy:items=%7C%7C*[class=article-content__title]/https://uanalyze.com.tw/articles",
            "https://morss.it/:proxy/https://www.macromicro.me/blog",
            "https://morss.it/:proxy/https://fintastic.trading/",
            ]
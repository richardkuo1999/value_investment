import re
import fitz
import docx
import logging
from DevFeat.news_parser import AsyncNewsParser
from Database.DB import DB
from utils.AI.GroqAI import GroqAI
from utils.telebot.config import NEWS_SOURCE_URLS

logger = logging.getLogger(__name__)
groq = GroqAI()
NewsParser = AsyncNewsParser()
db = DB()
NEWS_DATA = { news_type : [] for news_type in NEWS_SOURCE_URLS.keys() }
SUBSCRIBERS = set() # TODO saving to file or DB
ASK_CODE = 1

def is_valid_input(s: str) -> bool:
    return bool(re.fullmatch(r"[1-9][0-9]{3}", s))

def escape_markdown_v2(text: str) -> str:
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + c if c in escape_chars else c for c in text])

def group_news_title(data: str) -> str | None:
    if len(data) == 0:
        logger.warning(f"No news data found")
        return None
    text = "".join(f"📰[{escape_markdown_v2(article['title'])}]({article['url']})\n" for article in data)
    return text

def read_pdf(path):
    text = ""
    doc = fitz.open(path)
    for page in doc:
        text += page.get_text()
    return text

def read_word(path):
    doc = docx.Document(path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text
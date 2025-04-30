from telegram.ext import ContextTypes
import logging
import time
import asyncio

from utils.telebot.config import *
from utils.telebot.utils import *
from utils.telebot.handler import send_news
from utils.AI import GroqAI


# initial logger
logger = logging.getLogger(__name__)

async def get_news(context: ContextTypes.DEFAULT_TYPE):

    for news_type, url in NEWS_SOURCE_URLS.items():
        logger.info(f"NEWS SOURCE : {news_type}")
        news_list = await NewsParser.fetch_news_list(url) # Get news from parser only
        # TODO, ugly
        titles = [news['title'] for news in NEWS_DATA[news_type]]
        if len(titles) != 0:
            for ele in news_list:
                if ele['title'] not in titles and not SUBSCRIBERS:
                    logger.info("SEND NEWS")
                    await send_news(ele, context)
        else:
            logger.debug("No news")

        NEWS_DATA[news_type] = news_list # update news
        # update DB
        for news in news_list:
            db.checkNews(news)

    logger.info("Fetch news sources done")

async def get_reports(context: ContextTypes.DEFAULT_TYPE):

    logger.info("start")
    # 限制並行數量（例如每次最多同時執行 5 個任務）
    semaphore = asyncio.Semaphore(5)
    async def fetch_and_send_report(url):
        # 在 semaphore 內執行
        async with semaphore:
            # 獲取報告
            reports = await NewsParser.fetch_report(url)  # 假設 fetch_report 是異步的
            report = reports[0]
            exists = db.checkReport(report)

            if not exists:
                article = f"{report['title']}\n{report['url']}"
                await context.bot.send_message(chat_id=CONFIG['GroupID'], text=article)
                logger.debug("update report")

    # 使用 gather 並行處理所有報告
    tasks = [fetch_and_send_report(url) for url in REPORT_URLS]
    # 使用 asyncio.gather 並行執行所有任務
    await asyncio.gather(*tasks)


# TODO, following functions may needs to be refactored
# =============================================================================

async def scheduled_task(self, context: ContextTypes.DEFAULT_TYPE):
    chatbot = GroqAI()
    prompt = "100字摘要，重要數字也要，且使用繁體中文回答"

    job_data = context.job.data  # 這裡就是你當初設的資料
    chat_id = job_data["chat_id"]
    filenames = []

    for typ, news_list in self.news_data.items():
        filename = typ.replace(" ", "_") + ".md"
        filenames.append(filename)
        with open(filename, "w", encoding="utf-8") as f:
            for news in news_list:
                f.write(news['title'] + "\n")
                
                if 'content' in news.keys():
                    summary = chatbot.talk(prompt=prompt, content=news['content'], reasoning=True)
                    f.write(summary + "\n")
                else:
                    pass
                f.write(news['url'] + "\n")
                f.write('-----------' + "\n")
        await context.bot.send_document(chat_id=chat_id, document=filename)
        time.sleep(5)

# TODO, needs to be refactored
async def cmd_news_summary(update, context):
        context.job_queue.run_repeating(scheduled_task, interval=60*30, first=0, data={"chat_id": update.effective_chat.id})
        await update.message.reply_text("設定每 30 分鐘傳送摘要檔案！(content available only)")
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeAllGroupChats
from telegram import InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.ext import ConversationHandler, JobQueue
from sqlalchemy import select, exists
import asyncio
import yaml, asyncio, re


from utils.telebot.config import CONFIG
from utils.telebot.handler import *
from utils.telebot.utils import NewsParser
from utils.telebot.jobs import get_news, get_reports, get_podcasts, cmd_news_summary
from utils.Logger import setup_logger
from server_main import Individual_search
def clean_markdown(text):
    # 移除連結，只留文字
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # 移除粗體、斜體、底線、刪除線等標記
    text = re.sub(r'(\*|_|~|`)+', '', text)
    return text

class TelegramBot:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.l = ""
        self.bot_cmd = {"start" : "開始使用機器人", 
                        "help" : "使用說明",
                        "esti" : "估算股票", 
                        "news" : "查看新聞", 
                        "info" : "查詢公司資訊",
                        "subscribe" : "訂閱即時新聞",
                        "unsubscribe" : "取消訂閱即時新聞",
                        "news_summary" : "新聞摘要"}
        self.bot_token = CONFIG['TelegramToken'][0]
        self.logger.info("Bot init done")

    async def init(self):
        await NewsParser.init_session() 

    async def set_main_menu(self, application: Application):
        commands = []
        for k, v in self.bot_cmd.items():
            commands.append(BotCommand(k, v))

        await application.bot.set_my_commands(
            commands,
            scope=BotCommandScopeAllGroupChats()
        )
    async def set_main_menu(self, application):
        commands = []
        for k, v in self.bot_cmd.items():
            commands.append(BotCommand(k, v))

        await application.bot.set_my_commands(
            commands,
            scope=BotCommandScopeAllGroupChats()
        )
    async def run(self):

        # 初始化 Application
        
        application = Application.builder().token(yaml.safe_load(open('token.yaml'))["TelegramToken"][0]).build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("info", cmd_info)],
            states={
                ASK_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, cmd_handle_info)]
            },
            fallbacks=[CommandHandler("cancel", cmd_cancel)],
        )
        
        # 註冊處理命令
        application.add_handler(CommandHandler("start", cmd_start))
        application.add_handler(CommandHandler("help", cmd_help))
        application.add_handler(CommandHandler("esti", cmd_esti))
        application.add_handler(CommandHandler("news", cmd_news))
        application.add_handler(CommandHandler("uanalyze", cmd_uanalyze))
        application.add_handler(CommandHandler("subscribe", cmd_subscribe))
        application.add_handler(CommandHandler("unsubscribe", cmd_unsubscribe))
        application.add_handler(CommandHandler("news_summary", cmd_news_summary))
        application.add_handler(conv_handler)
        application.add_handler(CallbackQueryHandler(button_cb))
        # 錯誤處理
        application.add_error_handler(cmd_error)
        # repeat task
        # application.job_queue.run_repeating(callback=get_reports , interval=600, first=10, data={}, name="get_reports", job_kwargs={"misfire_grace_time": 5})
        # application.job_queue.run_repeating(callback=get_news, interval=60, first=10, data={}, name="get_news", job_kwargs={"misfire_grace_time": 5})
        application.job_queue.run_repeating(callback=get_podcasts, interval=60*60, first=10, data={}, name="get_podcasts", job_kwargs={"misfire_grace_time": 5})
        # 註冊文字訊息處理器，這會回應用戶發送的所有文字訊息
        application.add_handler(MessageHandler(filters.ALL, handle_message))
        await self.set_main_menu(application)
        # 開始輪詢
        self.logger.info("Bot start polling")
        await application.run_polling()

async def main():
    setup_logger(logging.INFO)
    MyBot = TelegramBot()
    await MyBot.init() # initialize NewsParser session
    await MyBot.run()

if __name__ == "__main__":
    asyncio.run(main())
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from groq import Groq
import yaml
import requests
import time
import asyncio
import threading

from server_main import Individual_search
from Database.MoneyDJ import MoneyDJ
from utils.AI import GroqAI
from DevFeat.news_parser import NewsParser

def shorten_url_tinyurl(long_url):
    api_url = "http://tinyurl.com/api-create.php"
    params = {'url': long_url}
    response = requests.get(api_url, params=params)
    return response.text

async def set_main_menu(application):
    commands = [
        BotCommand("start", "開始使用機器人"),
        BotCommand("info", "查看今日新聞"),
        BotCommand("esti", "新聞摘要"),
        BotCommand("help", "使用說明")
    ]
    await application.bot.set_my_commands(commands)

# 定義 /start 命令處理器
async def start(update: Update, context):
    # 檢查訊息來源是群組還是私人訊息
    if update.message.chat.type == "group":
        await update.message.reply_text(f"Hello, {update.message.chat.title}! I'm your bot.")
    else:
        await update.message.reply_text('Hello! I am your bot! How can I assist you today?')
# 定義 /help 命令處理器
async def help(update: Update, context):
    
    await update._bot.send_message(chat_id="-4769258504", text="help command")
    if update.message.chat.type == "group":
        await update.message.reply_text(f"In this group, I can assist you with commands like /start and /help.")
    else:
        await update.message.reply_text('To use this bot, just type a message, or use /start and /help.')

async def esti(update: Update, context):
    # print(context.args)
    stock_list = [x for idx, x in enumerate(context.args) if idx % 2 == 0]
    eps_list = [x for idx, x in enumerate(context.args) if idx % 2 != 0]
    # print(stock_list, eps_list)

    # 檢查訊息來源是群組還是私人訊息
    if update.message.chat.type == "group":
        await update.message.reply_text(f"Hello, {update.message.chat.title}! I'm your bot.")

        for (stock_id, eps) in zip(stock_list, eps_list):
            
            await update.message.reply_text(f"Estimate start: {stock_id}")
            data = Individual_search([stock_id], [eps]) #TODO
            await update.message.reply_text(f"Estimate done: {stock_id}")
    else:
        pass

async def info(update: Update, context):
    ticker = context.args[0] if context.args else None
    DJ = MoneyDJ()
    chatbot = GroqAI()
    wiki_result = DJ.get_wiki_result(ticker)
    condition = "重點摘要，營收占比或業務占比，有詳細數字的也要列出來"
    prompt = "\n" + condition  + "，並且使用繁體中文回答\n"

    content = chatbot.talk(prompt, wiki_result, reasoning=True)

    # 檢查訊息來源是群組還是私人訊息
    if update.message.chat.type == "group":
        await update.message.reply_text(content)
    else:
        await update.message.reply_text('To use this bot, just type a message, or use /start and /help.')

# async def news(update: Update, context):
async def send_news():

    url = 'https://udn.com/news/breaknews/1/5#breaknews'
    NP = NewsParser(url)
    bot = Bot(token=yaml.safe_load(open('token.yaml'))["TelegramToken"][0])
    if not hasattr(send_news, "title_last"):
        send_news.title_last = ""  # 初始化靜態變數

    res_list = NP.fetch_news_list('udn', news_number=1)
    for article in res_list:

        title = article['title']
        if title == send_news.title_last:
            break
        send_news.title_last = title

        text = f"📰[{title}]({article['url']})"
        short_url = shorten_url_tinyurl(article['url'])

        keyboard = [[InlineKeyboardButton("🔍 看摘要", callback_data=short_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await bot.send_message(chat_id=yaml.safe_load(open('token.yaml'))["ChatID"][0]
                                , text=text
                                ,parse_mode='MarkdownV2'
                                , reply_markup=reply_markup)
        

def send_news_forever():
    while True:
        asyncio.run(send_news())
        time.sleep(60) # 每分鐘發送一次新聞

# 定義普通文字訊息處理器
async def echo(update: Update, context):
    print(f"Received message: {update.message.text}")
    # 群組中的回應
    if update.message.chat.type == "group":
        await update.message.reply_text(f"Group Message: {update.message.text}")
    else:
        await update.message.reply_text(f'You said: {update.message.text}')

# 回傳摘要
async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ Callback handler triggered")
    groq = GroqAI()
    NP = NewsParser()
    query = update.callback_query
    user = query.from_user
    await query.answer(text="處理中...，以私人回覆方式傳送摘要")
    
    article = NP.fetch_news_content(query.data, website="udn")
    content = article['content']
    summary = groq.talk(prompt="幫我摘要內容200字以內", content=content, reasoning=True)

    await query.message._bot.send_message(chat_id=user.id, text=f"{article['title']}\n🧠 新聞摘要：\n{summary}")

# 定義錯誤處理器
async def error(update: Update, context):
    print(f"Error: {context.error}")

def main():
    # 設置你的 Token
    TOKEN = yaml.safe_load(open('token.yaml'))["TelegramToken"][0]

    # 初始化 Application
    application = Application.builder().token(TOKEN).build()
    # 註冊處理命令 /start 和 /help
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("esti", esti))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CallbackQueryHandler(summarize))

    # 註冊文字訊息處理器，這會回應用戶發送的所有文字訊息
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # 錯誤處理
    application.add_error_handler(error)

    # asyncio.run(set_main_menu(application))
    set_main_menu(application)

    thread = threading.Thread(target=send_news_forever)
    thread.daemon = True  # 這樣主程序退出時，這個 thread 也會自動退出
    thread.start()

    # 開始輪詢
    application.run_polling()

if __name__ == '__main__':
    # asyncio.run(send_news())
    main()


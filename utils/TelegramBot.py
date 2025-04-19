from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeAllGroupChats
from telegram import InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.ext import ConversationHandler, JobQueue
import yaml
import requests
import time
import asyncio
import threading

from server_main import Individual_search
from Database.MoneyDJ import MoneyDJ
from utils.AI import GroqAI
from DevFeat.news_parser import NewsParser

# Global variable
NP = NewsParser()
news_data = {}
lock = asyncio.Lock()
job_queue = JobQueue()
ASK_CODE = 1
subscribers = set()

def shorten_url_tinyurl(long_url):
    api_url = "http://tinyurl.com/api-create.php"
    params = {'url': long_url}
    response = requests.get(api_url, params=params)
    return response.text

def escape_markdown_v2(text: str) -> str:
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + c if c in escape_chars else c for c in text])

async def set_main_menu(application):
    commands = [
        BotCommand("start", "開始使用機器人"),
        BotCommand("info", "查看公司摘要"),
        BotCommand("esti", "估算股票"),
        BotCommand("news", "查看新聞"),
        BotCommand("help", "使用說明")
    ]
    await application.bot.set_my_commands(
        commands,
        scope=BotCommandScopeAllGroupChats()
    )

# 定義 /start 命令處理器
async def cmd_start(update: Update, context):
    # 檢查訊息來源是群組還是私人訊息
    if update.message.chat.type == "group":
        await update.message.reply_text(f"Hello, {update.message.chat.title}! I'm your bot.")
    else:
        await update.message.reply_text('Hello! I am your bot! How can I assist you today?')
# 定義 /help 命令處理器
async def cmd_help(update: Update, context):
    
    await update._bot.send_message(chat_id="-4769258504", text="help command")
    if update.message.chat.type == "group":
        await update.message.reply_text(f"In this group, I can assist you with commands like /start and /help.")
    else:
        await update.message.reply_text('To use this bot, just type a message, or use /start and /help.')
# /subscribe
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global subscribers
    chat_id = update.effective_chat.id
    subscribers.add(chat_id)
    await update.message.reply_text("✅ 已訂閱新聞通知！")
# /unsubscribe
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global subscribers
    chat_id = update.effective_chat.id
    subscribers.discard(chat_id)
    await update.message.reply_text("❌ 已取消訂閱。")
# /estimate
async def cmd_esti(update: Update, context):
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
# user key info_start
async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("請輸入股票代碼：")
    return ASK_CODE 

async def cmd_handle_info(update: Update, context):
    ticker = update.message.text.strip()
    msg = ""
    
    if ticker is None:
        msg = "[ERROR] missing ticker information"
        await update.message.reply_text(msg)
        return
    
    msg = f"你輸入的代碼是 {ticker}，幫你處理！"
    await update.message.reply_text(msg)
    DJ = MoneyDJ()
    chatbot = GroqAI()

    wiki_result = DJ.get_wiki_result(ticker)
    condition = "重點摘要，營收占比或業務占比，有詳細數字的也要列出來"
    prompt = "\n" + condition  + "，並且使用繁體中文回答\n"

    content = chatbot.talk(prompt, wiki_result, reasoning=True)
    file_name = str(ticker) + "_info.md"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(content)
    with open(file_name, "rb") as f:
        await update.message.reply_document(
            document=InputFile(f, filename=file_name),
            caption="這是你的報告 📄"
        )
    return ConversationHandler.END
# 定義普通文字訊息處理器
async def cmd_echo(update: Update, context):
    print(f"Received message: {update.message.text}")
    # 群組中的回應
    if update.message.chat.type == "group":
        await update.message.reply_text(f"Group Message: {update.message.text}")
    else:
        await update.message.reply_text(f'You said: {update.message.text}')
# button callback
async def button_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("✅ Callback handler triggered")
    global NP
    groq = GroqAI()
    query = update.callback_query
    
    # response = requests.head(query.data, allow_redirects=True) # 取得最終網址
    
    # article = NP.fetch_news_content(response.url)
    # content = article['content']
    # summary = groq.talk(prompt="幫我摘要內容200字以內", content=content, reasoning=True)
    if query.data in news_data.keys():
        await query.answer()
        text = ""
        data =news_data[query.data]
        for article in data:
            text += f"📰[{escape_markdown_v2(article['title'])}]({article['url']})\n"
        if text != "":
            text = escape_markdown_v2(query.data) + "\n" + text
            await query.edit_message_text(text=text,
                                          parse_mode='MarkdownV2',
                                          reply_markup=query.message.reply_markup)
    else:
        await query.answer(text="處理中...，以私人回覆方式傳送摘要")
        user = query.from_user
        pass
    # await query.message._bot.send_message(chat_id=user.id, text=f"{article['title']}\n🧠 新聞摘要：\n{summary}")
# 定義錯誤處理器
async def cmd_error(update: Update, context):
    print(f"Error: {context.error}")
# 取消對話
async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("已取消操作。")
    return ConversationHandler.END
# 定義發送新聞的函數
async def send_news(news):
    
    global news_data, subscribers
    bot = Bot(token=yaml.safe_load(open('token.yaml'))["TelegramToken"][0])
    for chat_id in subscribers:
        title = news['title']
        url   = news['url']
        titles = f"📰[{escape_markdown_v2(title)}]({url})\n"

        if titles != "":
            text = f"{titles}"
            await bot.send_message(chat_id=chat_id
                                    , text=text
                                    , parse_mode='MarkdownV2')

async def cmd_news(update: Update, context):
    global news_data
    buttons = []
    for key in news_data.keys():
        buttons.append(InlineKeyboardButton(key, callback_data=key))

    # keyboard = [[btn] for btn in buttons]
    keyboard = [buttons[i:i+3] for i in range(0, len(buttons), 3)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message._bot.sendMessage(chat_id=update.message.chat_id
                                        , text="請選擇新聞來源與類型"
                                        , reply_markup=reply_markup
                                        , parse_mode='MarkdownV2')

async def scheduled_task(context: ContextTypes.DEFAULT_TYPE):
    # job_data = context.job.data
    # chat_id = job_data['chat_id']
    # await context.bot.send_message(chat_id=chat_id, text="📢 定時訊息！")
    chatbot = GroqAI()
    prompt = "100字摘要，重要數字也要，且使用繁體中文回答"

    job_data = context.job.data  # 這裡就是你當初設的資料
    chat_id = job_data["chat_id"]
    filenames = []

    for typ, news_list in news_data.items():
        # print(typ, news_list)
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

async def cmd_news_summary(update, context):
    chat_id = update.message.chat_id
    context.job_queue.run_repeating(scheduled_task, interval=60*30, first=0, data={"chat_id": update.effective_chat.id})
    await update.message.reply_text("設定每 30 分鐘傳送摘要檔案！(content available only)")

async def get_news(urls):

    global NP, news_data, subscribers
    bot = Bot(token=yaml.safe_load(open('token.yaml'))["TelegramToken"][0])
    async with lock:
        for news_type, url in urls.items():
            print("NEWS SOURCE : ", news_type)
            res_list = NP.fetch_news_list(url, 10) # Get news from parser only
            titles = [news['title'] for news in news_data[news_type]]
            print(titles)
            if len(titles) != 0:
                for ele in res_list:
                    if ele['title'] not in titles:
                        print("SEND NEWS")
                        await send_news(ele)

            news_data[news_type] = res_list # update news

            print("Fetch done")

def get_news_forever():
    global news_data
    # set source 
    src_urls = {
            '[udn] 產業' : 'https://money.udn.com/rank/newest/1001/5591/1', 
            '[udn] 證券' : 'https://money.udn.com/rank/newest/1001/5590/1',
            '[udn] 國際' : 'https://money.udn.com/rank/newest/1001/5588/1',
            '[udn] 兩岸' : 'https://money.udn.com/rank/newest/1001/5589/1',
            '[moneydj] 發燒頭條' : 'https://www.moneydj.com/KMDJ/RssCenter.aspx?svc=NR&fno=1&arg=MB010000',
            'WSJ Chinese' : 'https://cn.wsj.com/zh-hans/rss',
            'Yahoo TW' : "https://tw.stock.yahoo.com/rss?category=news",
            "Investing Economy" : 'https://www.investing.com/rss/news_14.rss'}
    news_data = { news_type : [] for news_type in src_urls.keys() } # initial news_data

    while True:
        asyncio.run(get_news(src_urls))
        time.sleep(300) # 每300秒抓取一次新聞

def main():
    # 設置你的 Token
    TOKEN = yaml.safe_load(open('token.yaml'))["TelegramToken"][0]

    # 初始化 Application
    application = Application.builder().token(TOKEN).build()

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
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    
    application.add_handler(CommandHandler("news_summary", cmd_news_summary))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_cb))
    # 錯誤處理
    application.add_error_handler(cmd_error)
    # 註冊文字訊息處理器，這會回應用戶發送的所有文字訊息
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # asyncio.run(set_main_menu(application))
    set_main_menu(application)

    threading.Thread(target=get_news_forever, daemon=True).start()
    # threading.Thread(target=news_publisher, args=(application,), daemon=True).start()

    # 開始輪詢
    application.run_polling()

if __name__ == '__main__':
    main()


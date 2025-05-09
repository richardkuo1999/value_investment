from telegram import InputFile, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, ConversationHandler
import logging
import traceback
import io
import asyncio
from utils.telebot.utils import *
from utils.AI.GeminiAI import GeminiReqeustType
from utils.telebot.config import CONFIG
from Database.MoneyDJ import MoneyDJ


# initial logger
logger = logging.getLogger(__name__)
# ===============Basic Command Handler===================
# 定義 /start 命令處理器
async def cmd_start(update: Update, context):
    await update.message.reply_text('Hello! I am your bot! How can I assist you today?')
# 定義 /help 命令處理器
async def cmd_help(update: Update, context):
    group_id = CONFIG['GroupID'][0]
    await context.bot.send_message(chat_id=group_id, text="help command")
    if update.message.chat.type == "group":
        await update.message.reply_text(f"In this group, I can assist you with commands like /start and /help.")
    else:
        await update.message.reply_text('To use this bot, just type a message, or use /start and /help.')
# 定義錯誤處理器
async def cmd_error(update: Update, context):
    tb = "".join(traceback.format_exception(None, context.error, context.error.__traceback__))
    # 嘗試抓使用者資料和輸入的指令
    user = None
    command_text = None

    if isinstance(update, Update):
        user = update.effective_user
        if update.message:
            command_text = update.message.text
        elif update.callback_query:
            command_text = update.callback_query.data
            
    logger.error(
        # f"❌ Error from user={user.id if user else 'Unknown'} "
        # f"name={user.full_name if user else 'N/A'}\n"
        f"\n👉 Command/Text: {command_text}\n"
        f"🪵 Traceback:\n{tb}"
    )
    
# 取消對話
async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("已取消操作。")
    return ConversationHandler.END

async def cmd_uanalyze(update: Update, context):

    reports = NewsParser.get_uanalyze_report()
    for rep in reports:
        text = f"📰{rep['title']}\n{rep['link']}"
        await update.message._bot.sendMessage(chat_id=update.message.chat_id, text=text)
# /subscribe
async def cmd_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    SUBSCRIBERS.add(chat_id)
    await update.message.reply_text("✅ 已訂閱新聞通知！")
# /unsubscribe
async def cmd_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    SUBSCRIBERS.discard(chat_id)
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
            # data = Individual_search([stock_id], [eps]) #TODO
            await update.message.reply_text(f"Estimate done: {stock_id}")
    else:
        pass
# user key info_start
async def cmd_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("🔎 請輸入股票代碼：")
    return ASK_CODE 

async def cmd_handle_info(update: Update, context):
    ticker = update.message.text.strip()
    res = is_valid_input(ticker)
    msg = ""
    
    if ticker is None or res is False:
        msg = "[ERROR] Wrong ticker information"
        await update.message.reply_text(msg)
        return ConversationHandler.END
    
    msg = f"✅ 你輸入的代碼是 {ticker}，幫你處理！📊"
    await update.message.reply_text(msg)
    DJ = MoneyDJ()

    data = await DJ.get_wiki_result(ticker)
    ticker_name, wiki_result = data
    # error handle
    logger.info("get wiki_result")
    if ticker_name is None or wiki_result is None:
        await update.message.reply_text(f"Information of Ticker {ticker} is not found.")
    else:
        condition = "近1年的公司產品、營收占比、業務來源、財務狀況(營收、eps、毛利率等)\
                    、近期pros & cons 加上 google 搜尋結果，要幫我標示來源"
        prompt = "\n" + condition  + "，並且使用繁體中文回答\n"
        # content = groq.talk(prompt, wiki_result, reasoning=True)
        content = await gemini.call(text=wiki_result, prompt=prompt, RQtype=GeminiReqeustType.TEXT)
        if content is None:
            logger.error(content)
            await update.message.reply_text("抱歉我壞了")
        else:
            # logger.debug(content)
            file_name = f"{str(ticker)}{ticker_name}_info.md"
            buffer = io.BytesIO()
            buffer.write(content.encode('utf-8'))
            buffer.seek(0)  # 回到開頭供 Telegram 使用

            await update.message.reply_document(
                document=InputFile(buffer, filename=file_name),
                caption="這是你的報告(含google搜尋) 📄"
            )
    return ConversationHandler.END

async def cmd_googleNews(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("請輸入想查詢 Google 新聞的內容：")
    return ASK_CODE

async def cmd_handle_googleNews(update: Update, context):
    keyword = update.message.text.strip()
    url = f"https://news.google.com/rss/search?q={keyword}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    data = await NewsParser.rss_parser(url)
    data.sort(key=lambda x: x["pubTime"] or "", reverse=True)
    text = group_news_title(data[:10])
    await update.message.reply_text(text=text,
                                    parse_mode='MarkdownV2')
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
    logger.debug("✅ Callback handler triggered")
    query = update.callback_query
    
    if query.data in NEWS_DATA.keys(): # Send news back to reply button
        logger.debug(f"Query data: {query.data}")
        await query.answer()
        data = NEWS_DATA[query.data]
        text = group_news_title(data)

        if text is not None:
            logger.debug(f"Send news to user")
            text = escape_markdown_v2(query.data) + "\n" + text
            await query.edit_message_text(text=text,
                                        parse_mode='MarkdownV2',
                                        disable_web_page_preview=True,
                                        reply_markup=query.message.reply_markup)
        else:
            logger.warning("No news data can be sent")
    else:
        await query.answer(text="處理中...，以私人回覆方式傳送摘要")
        # user = query.from_user
        # pass
        # await query.message._bot.send_message(chat_id=user.id, text=f"{article['title']}\n🧠 新聞摘要：\n{summary}")

async def cmd_news(update: Update, context):
    buttons = [InlineKeyboardButton(key, callback_data=key) for key in NEWS_DATA.keys()]
    keyboard = [buttons[i:i+3] for i in range(0, len(buttons), 3)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message._bot.sendMessage(chat_id=update.message.chat_id
                                        , text="請選擇新聞來源與類型"
                                        , reply_markup=reply_markup
                                        , parse_mode='MarkdownV2')

# 定義發送新聞的函數, TODO
async def send_news(news, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("send_news to subscriber")
    for chat_id in SUBSCRIBERS:
        title = news['title']
        url   = news['url']
        titles = f"📰[{escape_markdown_v2(title)}]({url})\n"
        await context.bot.send_message(chat_id=chat_id
                                    , text=titles
                                    , parse_mode='MarkdownV2')

research_group = []

async def  cmd_research(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("📚 請提供欲研究之資料，📝 文字與 📎 檔案皆可（可多份）：")
    return 1

async def cmd_handle_research(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global research_group
    
    if update.message.document:
        document = update.message.document
        file_name = document.file_name.lower()
        logger.debug(f"File name: {file_name}")
        # 判斷副檔名
        if not file_name.endswith((".docx", ".doc", ".pdf")):
            await update.message.reply_text("這個檔案格式我還不支援喔！")
            return
        
        file = await document.get_file()   # 第一次 await，拿到檔案物件
        # 將檔案下載到記憶體中的 BytesIO
        bio = io.BytesIO()
        await file.download_to_memory(out=bio)
        bio.seek(0)
        typ = ""
        if file_name.endswith('.doc') or file_name.endswith('.docx'):
            from docx import Document
            doc = Document(bio)
            content = "\n".join([para.text for para in doc.paragraphs])
            bio = io.BytesIO(content.encode('utf-8'))
            bio.seek(0)
            typ = "text/plain"
        else:
            typ = "application/pdf"
            
        content = bio.getvalue()
        research_group.append((typ, content))
    elif update.message.text:
        text = update.message.text
        if len(text) > 200:
            bio = io.BytesIO(text.encode('utf-8'))
            bio.seek(0)
            research_group.append(("text/plain", bio.getvalue()))
        
    """
    elif update.message.photo:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        await context.bot.send_photo(chat_id=group_id, photo=file.file_id) # 直接轉傳

    elif update.message.text:
        text = update.message.text
        if "call memo" in text.lower() or "memo" in text.lower():
            await context.bot.send_message(chat_id=group_id, text=f"有用戶傳了Call Memo給我，幫你摘要內容")
            prompt = "幫我做重點摘要500字以內，重點數字優先"
            summary = await gemini.call(RQtype=GeminiReqeustType.TEXT, text=text, prompt=prompt)
            file_path = "./summary.md"
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(summary)
            with open(file_path, "rb") as file:
                await context.bot.send_document(chat_id=group_id, document=file, caption="這是你的摘要 📄")
            os.remove(file_path)
        else:
            pass
            # await update.message.reply_text("你傳了一段文字。")
    else:
        pass
        # await update.message.reply_text("這種類型我還看不懂喔。")
    """
    
async def cmd_research_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    global research_group
    sent_msg = await update.message.reply_text("開始為你生成研究報告資訊📊📄(預設prompt)")
    await asyncio.sleep(5) # 等待幾秒鐘確保傳輸完成
    # default prompt
    prompt = "根據提供的報告整理出 8 個常見投資問題與詳細回答，並用繁體中文回答"
    summary = await gemini.call(RQtype=GeminiReqeustType.FILE, prompt=prompt, contents=research_group)
    research_group = [] # clear list
    bio = io.BytesIO(summary.encode("utf-8"))
    bio.seek(0)
    bio.name = "Research.md"
    await update.message.reply_document(document=InputFile(bio), filename="Research.md", reply_to_message_id=sent_msg.message_id)
    return ConversationHandler.END
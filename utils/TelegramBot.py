from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from server_main import Individual_search
from Database.MoneyDJ import MoneyDJ
from groq import Groq
import yaml

# 定義 /start 命令處理器
async def start(update: Update, context):
    # 檢查訊息來源是群組還是私人訊息
    if update.message.chat.type == "group":
        await update.message.reply_text(f"Hello, {update.message.chat.title}! I'm your bot.")
    else:
        await update.message.reply_text('Hello! I am your bot! How can I assist you today?')

# 定義 /help 命令處理器
async def help(update: Update, context):
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
    GROQ_API_KEY = yaml.safe_load(open('token.yaml'))["GROQ_API_KEY"][0]
    DJ = MoneyDJ()
    groq = Groq(api_key=GROQ_API_KEY)

    wiki_result = DJ.get_wiki_result(ticker)
    # condition = "幫我摘要內容成 5 個要點"
    condition = "重點摘要，營收占比或業務占比，有詳細數字的也要列出來"
    # condition = "幫我找出投資機會"
    prompt = "\n" + condition  + "，並且只能用繁體中文回答。\n"
    response = groq.chat.completions.create(
        model = 'llama3-70b-8192',
        messages=[
            {"role": "user", "content": wiki_result + prompt},
        ]
    )
    content = response.choices[0].message.content

    # 檢查訊息來源是群組還是私人訊息
    if update.message.chat.type == "group":
        await update.message.reply_text(content)
    else:
        await update.message.reply_text('To use this bot, just type a message, or use /start and /help.')
        
# 定義普通文字訊息處理器
async def echo(update: Update, context):
    print(f"Received message: {update.message.text}")
    # 群組中的回應
    if update.message.chat.type == "group":
        await update.message.reply_text(f"Group Message: {update.message.text}")
    else:
        await update.message.reply_text(f'You said: {update.message.text}')

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

    # 註冊文字訊息處理器，這會回應用戶發送的所有文字訊息
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # 錯誤處理
    application.add_error_handler(error)

    # 開始輪詢
    application.run_polling()

if __name__ == '__main__':
    main()

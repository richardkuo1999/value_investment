import pandas as pd
import requests
import fitz  # PyMuPDF
import re
from tqdm import tqdm
from utils.AI import GroqAI
from utils.Logger import setup_logger

client = GroqAI()
logger = setup_logger()

def download_pdf(link, output_path="downloaded.pdf"):
    # print(link)
    # 使用正則表達式提取 file_id
    file_id = re.search(r'/d/([a-zA-Z0-9_-]+)', link)
    if file_id:
        logger.debug(f"File ID: {file_id.group(1)}")
    else:
        logger.error("無法提取 File ID")

    download_url = f'https://drive.google.com/uc?export=download&id={file_id.group(1)}'
    logger.debug(f"Download URL: {download_url}")
    response = requests.get(download_url, stream=True)
    
    # 檢查請求是否成功
    if response.status_code == 200:
        # 儲存檔案為 PDF
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=128):
                f.write(chunk)
        logger.debug("PDF 下載完成!")
        return True
    else:
        logger.error(f"下載失敗，錯誤碼: {response.status_code}")
        return False
    
def extract_pdf():
    text = ""
    with fitz.open("downloaded.pdf") as doc:        
        for page in doc:
            text += page.get_text()
            logger.warning("Read first page only")
            break # 只讀取第一頁
    return text

def search_excel(stock_id):

    # Google Sheets 的 ID 和 GID（工作表 ID）
    sheet_id = "15UhRGMsukVopC2QExKQrJ1AmWiD24UZKPJ55s-owmKg"
    gid = "0"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    logger.warning(f"This excel format will be changed, please check the link when error occurs.")
    # 使用新版 pandas 的參數
    df = pd.read_csv(url, on_bad_lines='skip', engine='python')
    columns = list(df.columns)

    # 將最後1個欄位名稱改為 'Report Link'
    columns[-1] = 'Report Link'
    df.columns = columns

    df_filtered = df[df['股票代號'].astype(str).str.contains(stock_id, na=False)]

    # 顯示資料（可依需要儲存或分析）
    res_report_link = df_filtered['Report Link'].tolist()
    return res_report_link

def chunk_text(text, max_length=7000):
    """將文本分割成最大長度為 max_length 的片段"""
    words = text.split()
    chunks = []
    current_chunk = []
    
    for word in words:
        current_chunk.append(word)
        if len(' '.join(current_chunk)) > max_length:
            chunks.append(' '.join(current_chunk[:-1]))  # 創建新片段
            current_chunk = [word]  # 重設
    if current_chunk:
        chunks.append(' '.join(current_chunk))  # 加入最後一個片段
    
    return chunks


def summarize(chunk):
    global client
    try:
        condition = "重點摘要，營收占比或業務占比，有詳細數字的也要列出來"
        prompt = "\n" + condition  + "，並且使用繁體中文回答。\n"
        
        response = client.talk(prompt, chunk, reasoning=True)
        return response
    
    except Exception as e:
        logger.error(f"摘要失敗: {e['error']['code'], e['error']['message']}")
        return ""

def main():
    ticker = '2330'
    search_result = search_excel(ticker)
    summarize_list = []
    for idx, link in enumerate(search_result):
        sts = download_pdf(link)
        if sts:
            text = extract_pdf()
            chunks = chunk_text(text)
            for chunk in tqdm(chunks):
                res = summarize(chunk)
                summarize_list.append(res)

        if idx == 7 : # 只讀取前8個報告
            logger.warning("Read first 5 reports only")
            break

    summary_all = "\n".join(summarize_list)
    print(len(summary_all))
    logger.info(f"Summarize again")
    summary = summarize(summary_all)
    logger.info(f"Summarize: {summary}")

if __name__ == "__main__":
    main()
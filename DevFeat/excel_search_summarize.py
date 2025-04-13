import pandas as pd
import requests
import fitz  # PyMuPDF
import re
from tqdm import tqdm
from groq import Groq
import yaml

GROQ_API_KEY = yaml.safe_load(open('token.yaml'))["GROQ_API_KEY"][0]
client = Groq(api_key=GROQ_API_KEY)

def download_pdf(link, output_path="downloaded.pdf"):
    # print(link)
    # 使用正則表達式提取 file_id
    file_id = re.search(r'/d/([a-zA-Z0-9_-]+)', link)
    if file_id:
        print("File ID:", file_id.group(1))
    else:
        print("無法提取 File ID")

    download_url = f'https://drive.google.com/uc?export=download&id={file_id.group(1)}'
    print(download_url)
    response = requests.get(download_url, stream=True)
    
    # 檢查請求是否成功
    if response.status_code == 200:
        # 儲存檔案為 PDF
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=128):
                f.write(chunk)
        print("PDF 下載完成!")
        return True
    else:
        print("下載失敗，錯誤碼:", response.status_code)
        return False
    
def extract_pdf():
    text = ""
    with fitz.open("downloaded.pdf") as doc:        
        for page in doc:
            text += page.get_text()
    return text

def search_excel(stock_id):

    # Google Sheets 的 ID 和 GID（工作表 ID）
    sheet_id = "15UhRGMsukVopC2QExKQrJ1AmWiD24UZKPJ55s-owmKg"
    gid = "0"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

    # 使用新版 pandas 的參數
    df = pd.read_csv(url, on_bad_lines='skip', engine='python')
    columns = list(df.columns)

    # 將最後兩個欄位名稱改為 'Report Link' 和 'Count'
    columns[-2] = 'Report Link'
    columns[-1] = 'Count'
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


def summarize_chunk(chunk):
    global client
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "你是一位摘要助手，擅長將長文章壓縮成精簡摘要。"},
                {"role": "user", "content": f"請幫我摘要，且只能用中文回答我：\n{chunk}"}
            ]
        )
        res = response.choices[0].message.content
        return res
    except Exception as e:
        print("摘要失敗:", e)
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
                res = summarize_chunk(chunk)
                summarize_list.append(res)
                # print(res)

        if idx == 0: # 逐步測試
            break
    for summary in summarize_list:
        print(summary)


if __name__ == "__main__":
    main()
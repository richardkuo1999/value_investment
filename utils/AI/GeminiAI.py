import time
import yaml
import asyncio
import logging
import functools
from enum import Enum
from pathlib import Path
from google import genai
from google.genai import types
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
from google.api_core.exceptions import ServiceUnavailable, ServerError

from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from utils.utils import log_retry_attempt, is_file_exists


# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiReqeustType(Enum):
    TEXT = 1
    IMAGE = 2
    FILE = 3
    AUDIO = 4
    VIDEO = 5

def async_timer(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        end = time.time()
        logger.info(f"{func.__name__} 執行時間: {end - start:.4f} 秒")
        return result
    return wrapper

class geminiAI():

    def __init__(self):
        self.key_idx = 0 # record the key index
        self.key_list = yaml.safe_load(open('token.yaml'))["GEMINI_API_KEY"]
        self.client = self.get_client()
        # sort by performance
        self.model_list = ["gemini-1.5-flash-8b", "gemini-1.5-flash", "gemini-2.0-flash-lite",
                           "gemini-2.0-flash", "gemini-2.5-flash-preview-04-17", "gemini-1.5-pro",
                        #    "gemini-2.5-pro-preview-03-25"         # free tier can't use this model
                           ]
        self.model_idx = 4 # default model index
        self.model_name = self.model_list[self.model_idx]
        logger.info(f"Current model: {self.model_name}")

    def switch_model(self, plus=True) -> bool:
        self.model_idx =  self.model_idx+1 if plus else self.model_idx-1
        if self.model_idx < 0:
            print("已經是最弱模型了")
            self.model_idx = 0
            return False
        elif self.model_idx >= len(self.model_list):
            print("已經是最強模型了")
            self.model_idx = len(self.model_list) - 1
            return False
        else:
            self.model_name = self.model_list[self.model_idx]
            logger.info(f"Switch to model {self.model_name}")
            return True
    
    def get_client(self):
        self.key_idx = self.key_idx + 1 if (self.key_idx + 1) < len(self.key_list) else 0
        logger.info(f"Switch to key index {self.key_idx}")
        api_key = self.key_list[self.key_idx]
        return genai.Client(api_key=api_key)
        

    @async_timer
    async def __query_text(self, path: Path, prompt: str | None) -> str | None:
        with open(path,'r') as f:
            text = f.read() #沒指定size

        prompt = f"用中文摘要這份報告: {text}" if prompt is None else f"{prompt}: {text}"

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=[prompt],
        )
        return response.text
    
    @async_timer
    async def __query_img(self, path: Path, prompt: str | None) -> str | None:
        
        # prompt = "用中文摘要這張照片"
        prompt = "給這張照片一個標題，並且用中文描述這張照片的內容，格式如下:\n標題：\n內容："  if prompt is None else prompt

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(
                    data=path.read_bytes(),
                    mime_type='image/jpeg',
                ),
                prompt,
                ]
        )
        return response.text

    @async_timer
    async def __query_file(self, path: Path, prompt: str | None) -> str | None:
        # Retrieve and encode the PDF byte
        
        prompt = "用中文條列重點這份文件，幫我做質化分析跟量化分析，並且幫我做SWOT分析，還有幫我做PEST分析，最後幫我做5 Forces分析。" if prompt is None else prompt
        # prompt = "幫我做重點摘要500字以內，重點數字優先"
        # prompt = "你是一位專業分析師，請根據以下文件提取出：\n文章主題\n核心觀點（2~5 點）\n支持觀點的關鍵資料或引用\n結論或作者建議（若有），並且幫我做SWOT分析，還有幫我做PEST分析，最後幫我做5 Forces分析。"
        prompt = input("query: ")
        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(
                    data=path.read_bytes(),
                    mime_type="application/pdf",
                ),
                prompt,
            ],
        )
        return response.text
 
    @async_timer
    async def __query_audio(self, path: Path, prompt: str | None) -> str | None:

        # prompt = "用中文條列與投資市場相關的資訊跟重點，以及對於投資市場的看法或操作建議，並照以下格式輸出給我:\
        #           1. 總體經濟與市場動向 \n 2.產業與個股剖析 \n 3. 個人的市場操作與建議"  if prompt is None else prompt
        prompt = "請提取以下細節：\
            1. 提出Podcast中討論的主要股市投資策略，每個策略的細節、優缺點以及適用的情況。\
            2. 解釋主持人如何看待當前股市的整體走勢，並分析未來可能的市場趨勢。\
            3. 詳細描述主持人對於風險管理的建議，並列出實際的操作方法，例如如何分散風險或管理市場波動。\
            4. 如果Podcast中提到過任何具體的股票或行業，請提供對這些股票或行業的深入分析，包括投資的原因、風險以及預期回報。\
            5. 討論Podcast中有關行為金融學或投資者心理學的部分，說明主持人如何解釋情緒和決策如何影響投資行為。\
            6. 如果主持人分享過自己的成功或失敗經歷，請提供這些經歷並說明其中的學習點。\
            ，並照以下格式條列輸出給我: 1. 總體經濟與市場動向 \n 2.產業與個股剖析 \n 3. 個人的市場操作與建議"
        # google_search_tool = Tool(
        # google_search = GoogleSearch()
        # )
        with open(path, 'rb') as f:
            audio_bytes = f.read()

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=[
                prompt,
                types.Part.from_bytes(
                data=audio_bytes,
                mime_type='audio/mp3',
                )
            ],
            # config=GenerateContentConfig(
            #     tools=[google_search_tool],
            #     response_modalities=["TEXT"],
            # )
        )
        return response.text

    @async_timer
    async def __query_video(self, path: Path, prompt: str | None) -> str | None:

        prompt = "用中文條列重點這份影片" if prompt is None else prompt
        
        with open(path, 'rb') as f:
            video_bytes = f.read()

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=types.Content(
                parts=[
                    types.Part(
                        inline_data=types.Blob(data=video_bytes, mime_type='video/mp4')
                    ),
                    types.Part(text=prompt)
                ]
            )
        )
        return response.text
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(5),
        retry=retry_if_exception_type((ServiceUnavailable, ServerError)),
        before_sleep=log_retry_attempt,
    )
    # Universal interface for call gemini model
    async def call(
        self,
        path: Path,
        text: str | None,
        RQtype: GeminiReqeustType,
        prompt: str | None = None
    ):
        if not is_file_exists(path):
            raise FileNotFoundError(f"File {path} not found.")

        match RQtype:
            case GeminiReqeustType.TEXT:
                response = await self.__query_text(path=path, prompt=prompt)
                return response
            case GeminiReqeustType.IMAGE:
                response = await self.__query_img(path=path, prompt=prompt)
                return response
            case GeminiReqeustType.FILE:
                response = await self.__query_file(path=path, prompt=prompt)
                return response
            case GeminiReqeustType.AUDIO:
                response = await self.__query_audio(path=path, prompt=prompt)
                return response
            case GeminiReqeustType.VIDEO:
                response = await self.__query_video(path=path, prompt=prompt)
                return response
            case _:
                raise NotImplementedError(f"Request type {RQtype} not implemented.")


async def main(path, RQtype, text=None):
    if not is_file_exists(path):
        raise FileNotFoundError(f"File {path} not found.")
    
    AI = geminiAI()
    ret_data = await AI.call(path=path, text=text, RQtype=RQtype)
    print(ret_data)

if __name__ == "__main__":
    while True:
        for member in GeminiReqeustType:
            print(f"{member.value}. {member.name}")

        try:
            path, text = None, None
            choice = input("請輸入對應的數字： ")
            request_value = int(choice)
            for member in GeminiReqeustType:
                if member.value == request_value:
                    if member == GeminiReqeustType.TEXT:
                        path = Path("reports", "test.text")
                    elif member == GeminiReqeustType.IMAGE:
                        path = Path("reports", "test.png")
                    elif member == GeminiReqeustType.FILE:
                        path = Path("reports", "test.pdf")
                    elif member == GeminiReqeustType.AUDIO:
                        # path = Path("reports", "test.mp3")
                        path = Path("./", "[Gooaye 股癌] 553.EP553  🦨.mp3")
                    elif member == GeminiReqeustType.VIDEO:
                        path = Path("reports", "test.mp4")
                    asyncio.run(main(path, member, text))
        except ValueError:
            logger.error("輸入格式錯誤，請輸入數字。")
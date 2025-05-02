import asyncio
import aiohttp
import aiofiles
import feedparser
import json
import logging

import os

DOWNLOAD_DIR = "podcasts"  # 下載資料夾
"""
Get id flow(2025/04/30):
1. Search podcast in apple podcast
2. Go to the home page of the podcast
3. Check the url, end of url is: idXXXXXXXXXXX
4. The XXXXXXXXXXX is the podcast id
5. using LOOK_UP_URL(folloing url ) + id to get feedurl( check detail by function **get_feed_url** )
"""
# source: Gooaye, 財女, 皓角
source_id = ['1500839292','1546879892', '1488295306']
LOOK_UP_URL = "https://itunes.apple.com/lookup?id="

logger = logging.getLogger(__name__)

# === Step 1: 從 iTunes API 抓出 feedUrl ===
async def get_feed_url(session, api_url) -> tuple | None:
    try:
        async with session.get(api_url) as resp:
            text = await resp.text()
            data = json.loads(text)  # 手動解析 JSON
            feed_url = data["results"][0]["feedUrl"]
            podcast_name = data["results"][0]["collectionName"]
            logger.debug(f"✅ 取得 feedUrl：{feed_url}")
            return (podcast_name, feed_url)
    except Exception as e:
        logger.error(f"❌ 解析失敗：{api_url} - {e}")
        return None

# === Step 2: 從 feedUrl 抓取 MP3 並下載 ===
async def download_mp3(session, url, filename):
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            async with aiofiles.open(filepath, 'wb') as f:
                await f.write(await response.read())
            logger.debug(f"🎧 下載完成：{filename}")
    except Exception as e:
        logger.error(f"❌ 下載失敗：{filename} - {e}")

async def download_from_feed(session, feed):
    try:
        podcast_name, feed_url = feed
        feed = feedparser.parse(feed_url)
        tasks = []
        for entry in feed.entries:
            title = entry.title.replace(" ", "_").replace("/", "_")  # 安全檔名
            enclosure = entry.get("enclosures") or []
            if enclosure:
                mp3_url = enclosure[0].get("href")
                if mp3_url:
                    filename = f"{podcast_name}_{title}.mp3"
                    tasks.append(download_mp3(session, mp3_url, filename))
            break # download 1 file only
        await asyncio.gather(*tasks)
    except Exception as e:
        logger.error(f"❌ RSS 錯誤：{feed_url} - {e}")

# === Step 3: 主程式 ===
async def main_process():
    logger.info("開始下載 Podcast")
    async with aiohttp.ClientSession() as session:
        # 抓 feedUrls
        feed_tasks = [get_feed_url(session, f"{LOOK_UP_URL}{id}") for id in source_id]
        feed_urls = await asyncio.gather(*feed_tasks)
        feed_urls = [data for data in feed_urls if data]

        # 抓 MP3
        all_tasks = [download_from_feed(session, feed) for feed in feed_urls]
        await asyncio.gather(*all_tasks)
    logger.info("Podcast 下載完成")

if __name__ == "__main__":
    asyncio.run(main_process())


import asyncio
from utils.analytics import AnalyticsProcessor
from utils.crawler import Crawler
from utils.fts_processor import FTSProcessor
from datetime import datetime

async def update_submissions() -> None:

    # datetime object containing current date and time
    now = datetime.now()

    print("now =", now)

    import nltk
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('corpus')
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", dt_string)
    print("Crawling")
    crawler = Crawler(verbose=True)
    await crawler.process()

    ap = AnalyticsProcessor(verbose=True)
    print("Processing submissions")
    await ap.process()

    oap = OpenAIProccessor(verbose=False)
    await oap.process()

    fts = FTSProcessor()
    fts.process()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(update_submissions())

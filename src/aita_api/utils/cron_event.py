import asyncio

from aita_api.utils.analytics import AnalyticsProcessor
from aita_api.utils.crawler import Crawler


async def update_submissions() -> None:
    print("Crawling")
    crawler = Crawler(verbose=True)
    await crawler.process()

    ap = AnalyticsProcessor(verbose=True)
    print("Processing submissions")
    await ap.process()

    # oap = OpenAIProccessor(verbose=False)
    # await oap.process()

    # fts = FTSProcessor()
    # fts.process()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(update_submissions())

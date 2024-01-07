from fastapi import FastAPI
from endpoints.health_api import HealthAPI
from utils.analytics import AnalyticsProcessor
from utils.crawler import Crawler

from endpoints.comment_api import CommentAPI

from fastapi.middleware.cors import CORSMiddleware
from endpoints.database_config import DatabaseConfig
from endpoints.openai_inference_api import OpenAIInferenceAPI
from endpoints.submission_api import SubmissionAPI
from endpoints.summary_api import SummaryAPI

from fastapi_utilities import repeat_every

from utils.process_openai import OpenAIProccessor


app = FastAPI(
    title="AITA API",
    description="API For AITA Subreddit",
    version="2.0.0",
)

# Configure origins for CORS
origins = [
    "http://localhost",
    "http://localhost:9001",
]

# Configure middleware for origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


database_config = DatabaseConfig()
engine = database_config.get_engine()


health_api = HealthAPI(engine)
submission_api = SubmissionAPI(engine)
openai_analysis_api = OpenAIInferenceAPI(engine)
comment_api = CommentAPI(engine)
summary_api = SummaryAPI(engine)


app.include_router(prefix="/api/v2", router=health_api.router)
app.include_router(prefix="/api/v2", router=submission_api.router)
app.include_router(prefix="/api/v2", router=comment_api.router)
app.include_router(prefix="/api/v2", router=openai_analysis_api.router)
app.include_router(prefix="/api/v2", router=summary_api.router)


@repeat_every(seconds=60 * 60)  # 1 hour
def updated_submissions() -> None:
    print("Crawling")
    crawler = Crawler()
    crawler.configure_agent()

    if crawler.validate_configuration is False:
        print("Invalid configuration")
        raise Exception("Invalid configuration.")

    crawler.crawl()
    ap = AnalyticsProcessor()
    print("Processing submissions")
    submissions = ap.get_submissions()
    ap.process(submissions)
    oap = OpenAIProccessor()
    oap.process(submissions)


app.add_event_handler("startup", updated_submissions)

import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utilities import repeat_every
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from endpoints.comment_api import CommentAPI
from endpoints.database_config import DatabaseConfig
from endpoints.health_api import HealthAPI
from endpoints.openai_inference_api import OpenAIInferenceAPI
from endpoints.submission_api import SubmissionAPI
from endpoints.summary_api import SummaryAPI
from utils.analytics import AnalyticsProcessor
from utils.crawler import Crawler
from utils.process_openai import OpenAIProccessor

app = FastAPI(
    title="AITA API",
    description="API For AITA Subreddit",
    version="2.0.0",
    contact={
        "email": "jianloongliew@gmail.com",
    },
    license_info={
        "name": "Apache 2.0",
        "identifier": "MIT",
    },
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

# app.add_middleware(PyInstrumentProfilerMiddleware)

# Limiters
limiter = Limiter(key_func=get_remote_address, default_limits=["20/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Database configuration
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


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@repeat_every(seconds=60 * 60)  # 1 hour
def update_submissions() -> None:
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


# app.add_event_handler("startup", update_submissions)

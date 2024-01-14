from time import time

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utilities import repeat_every
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
import uvicorn

from endpoints.comment_api import CommentAPI
from endpoints.database_config import DatabaseConfig
from endpoints.health_api import HealthAPI
from endpoints.openai_inference_api import OpenAIInferenceAPI
from endpoints.submission_api import SubmissionAPI
from endpoints.summary_api import SummaryAPI
from utils.fts_processor import FTSProcessor
from models.rate_limit import RateLimit
from utils.analytics import AnalyticsProcessor
from utils.crawler import Crawler
from utils.process_openai import OpenAIProccessor


class API:
    app = None

    def __init__(
        self, update: bool = False, use_test_db: bool = False, settings: dict = None
    ):
        self.app = FastAPI(
            title="AITA API",
            description="API For AITA Subreddit. All mutation end points are disabled by default.",
            version="2.0.0",
            contact={
                "email": "jianloongliew@gmail.com",
            },
            license_info={
                "name": "Apache 2.0",
                "identifier": "MIT",
            },
            swagger_ui_parameters={"operationsSorter": "method"},
        )

        self.use_test_db = use_test_db

        self.setup_routes()
        self.setup_limiter()
        self.setup_cors()

        self.setup_process_time()

        update is True and self.setup_startup_event()

    def setup_routes(self) -> None:
        # Database configuration
        database_config = DatabaseConfig(use_test_db=self.use_test_db)
        engine = database_config.get_engine()

        health_api = HealthAPI(engine)
        submission_api = SubmissionAPI(engine)
        openai_analysis_api = OpenAIInferenceAPI(engine)
        comment_api = CommentAPI(engine)
        summary_api = SummaryAPI(engine)
        # Add routers
        self.app.include_router(
            prefix="/api/v2",
            router=health_api.router,
            responses={status.HTTP_429_TOO_MANY_REQUESTS: {"model": RateLimit}},
        )
        self.app.include_router(
            prefix="/api/v2",
            router=submission_api.router,
            responses={status.HTTP_429_TOO_MANY_REQUESTS: {"model": RateLimit}},
        )
        self.app.include_router(
            prefix="/api/v2",
            router=comment_api.router,
            responses={status.HTTP_429_TOO_MANY_REQUESTS: {"model": RateLimit}},
        )
        self.app.include_router(
            prefix="/api/v2",
            router=openai_analysis_api.router,
            responses={status.HTTP_429_TOO_MANY_REQUESTS: {"model": RateLimit}},
        )
        self.app.include_router(
            prefix="/api/v2",
            router=summary_api.router,
            responses={status.HTTP_429_TOO_MANY_REQUESTS: {"model": RateLimit}},
        )

    def setup_cors(self):
        # Configure origins for CORS
        origins = ["*"]

        # Configure middleware for origins
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def setup_limiter(self) -> None:
        # Limiters
        limiter = Limiter(
            key_func=get_remote_address,
            headers_enabled=True,
            default_limits=["40/minute"],
        )
        self.app.state.limiter = limiter
        self.app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        self.app.add_middleware(SlowAPIMiddleware)

    def setup_startup_event(self) -> None:
        @repeat_every(seconds=60 * 60)  # 1 hour
        async def update_submissions() -> None:
            print("Crawling")
            crawler = Crawler(verbose=True)
            await crawler.process()

            ap = AnalyticsProcessor(verbose=False)
            print("Processing submissions")
            await ap.process()

            # oap = OpenAIProccessor(verbose=False)
            # await oap.process()

            fts = FTSProcessor()

            fts.process()

        self.app.add_event_handler("startup", update_submissions)

    def setup_process_time(self) -> None:
        @self.app.middleware("http")
        async def add_process_time_header(request: Request, call_next):
            start_time = time()
            response = await call_next(request)
            process_time = time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            return response


if __name__ == "__main__":
    api = API(update=True)

    uvicorn.run(api.app, host="0.0.0.0", port=8000, env_file="./env")

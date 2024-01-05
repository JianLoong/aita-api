from fastapi import FastAPI

from endpoints.comment_api import CommentAPI

from fastapi.middleware.cors import CORSMiddleware
from endpoints.database_config import DatabaseConfig
from endpoints.openai_inference_api import OpenAIInferenceAPI
from endpoints.static_api import StaticAPI
from endpoints.submission_api import SubmissionAPI
from endpoints.summary_api import SummaryAPI

app = FastAPI(title="AITA API", description="API For AITA Subreddit", version="2.0.0")

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

static_api = StaticAPI()
submission_api = SubmissionAPI(engine)
openai_analysis_api = OpenAIInferenceAPI(engine)
comment_api = CommentAPI(engine)
summary_api = SummaryAPI(engine)


app.include_router(prefix="/api/v2", router=submission_api.router)
app.include_router(prefix="/api/v2", router=comment_api.router)
app.include_router(prefix="/api/v2", router=openai_analysis_api.router)
app.include_router(prefix="/api/v2", router=summary_api.router)
app.include_router(prefix="/api/v2", router=static_api.router)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from endpoints.static_api import StaticAPI
from endpoints.comment_api import CommentAPI
from endpoints.openai_inference_api import OpenAIInferenceAPI
from endpoints.submission_api import SubmissionAPI
from endpoints.summary_api import SummaryAPI

app = FastAPI()

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

static_api = StaticAPI()
submission_api = SubmissionAPI()
openai_analysis_api = OpenAIInferenceAPI()
comment_api = CommentAPI()
summary_api = SummaryAPI()

app.include_router(prefix="/api/v2", router=submission_api.router)
app.include_router(prefix="/api/v2", router=comment_api.router)
app.include_router(prefix="/api/v2", router=openai_analysis_api.router)
app.include_router(prefix="/api/v2", router=summary_api.router)
app.include_router(prefix="/api/v2", router=static_api.router)

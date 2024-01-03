from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from endpoints.api import API

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

end_points = API()
app.include_router(end_points.router)

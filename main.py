from fastapi import FastAPI

from endpoints.api import API

app = FastAPI()
end_points = API()
app.include_router(end_points.router)

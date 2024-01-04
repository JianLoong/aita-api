import json
import logging
import os

from fastapi import APIRouter
from sqlmodel import SQLModel, create_engine


class StaticAPI:
    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def configure_database(self):
        self.sqlite_file_name = "AmItheAsshole.db"
        self.sqlite_url = f"sqlite:///database//{self.sqlite_file_name}"

        self.engine = create_engine(self.sqlite_url, echo=False)

    def __init__(self):
        logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

        self.configure_database()
        self.create_db_and_tables()
        self.router = APIRouter()

        self._setup_breakdown_routes()

    def _setup_breakdown_routes(self) -> None:
        self.router.add_api_route(
            "/search",
            self.read_search,
            methods=["GET"],
            tags=["Static Search Corpus"],
        )

    def read_search(self):
        with open(".//endpoints//static//search.json") as json_file:
            data = json.load(json_file)

            return data

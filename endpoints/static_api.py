import json
import logging
import os

from fastapi import APIRouter


class StaticAPI:
    def __init__(self):
        logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

        # self.configure_database()
        # self.create_db_and_tables()
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

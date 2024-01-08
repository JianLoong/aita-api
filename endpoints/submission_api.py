from enum import Enum
from random import randrange
from typing import List

import sqlalchemy
from fastapi import APIRouter, HTTPException, Query, Request, Response
from fuzzywuzzy import process
from sqlalchemy import Engine
from sqlmodel import Session, asc, desc, select

from models.submission import Submission

# from slowapi import Limiter, _rate_limit_exceeded_handler
# from slowapi.util import get_remote_address
# from slowapi.errors import RateLimitExceeded


class SubmissionAPI:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.router = APIRouter()

        self._setup_submission_routes()

    # Routes for submission
    def _setup_submission_routes(self) -> None:
        self.router.add_api_route(
            "/submissions",
            self.read_submissions,
            methods=["GET"],
            tags=["Submission"],
            description="Gets submissions from the database",
            responses={429: {"model": ""}},
        )
        self.router.add_api_route(
            "/submission/{id}",
            self.read_submission,
            methods=["GET"],
            tags=["Submission"],
            description="Gets submission from database based on id",
        )

        self.router.add_api_route(
            "/submisssions/search",
            self.search_submission,
            methods=["GET"],
            tags=["Submission"],
            status_code=200,
        )

        self.router.add_api_route(
            "/submissions/top",
            self.top_submission,
            methods=["GET"],
            tags=["Submission"],
            description="The top submission for each count of YTA, NTA and etc",
        )

        self.router.add_api_route(
            "/submissions/fuzzy-search",
            self.fuzzy_search,
            methods=["GET"],
            tags=["Submission"],
            description="Performs fuzzy seach on Id and Title",
        )

        self.router.add_api_route(
            "/submissions/random",
            self.random_submission,
            methods=["GET"],
            tags=["Submission"],
            description="Obtains a random submission",
        )

    # Enums for search submissions
    class _SubmissionSortBy(str, Enum):
        id = "id"
        score = "score"
        title = "title"
        created_utc = "new"

    class _OrderBy(str, Enum):
        asc = "asc"
        desc = "desc"

    def read_submission(self, id: int) -> Submission:
        with Session(self.engine) as session:
            submission = session.get(Submission, id)
            if not submission:
                raise HTTPException(status_code=404, detail="Submission not found")
            return submission

    def read_submissions(
        self,
        request: Request,
        response: Response,
        offset: int = Query(default=0, le=100),
        limit: int = Query(default=10, le=100),
        sort_by: _SubmissionSortBy = Query(
            alias="sortBy", default=_SubmissionSortBy.id
        ),
        order_by: _OrderBy = Query(alias="orderBy", default=_OrderBy.desc),
    ) -> List[Submission]:
        """
        Reads the submissions in the database.

        Args:
            offset (int): The offset
            limit (int): The limit
            sort_by (SubmissionSortBy or str): The sort by

        Returns:
            List[Submission]: Returns a list of submission. An empty list would  be returned if no results are found.

            Headers: X-Limit - The Limit used

        """
        match sort_by:
            case "id":
                sort = Submission.id
            case "title":
                sort = Submission.title
            case "score":
                sort = Submission.score
            case _:
                sort = Submission.id

        match order_by:
            case "desc":
                order = desc
            case "asc":
                order = asc
            case _:
                order = desc

        with Session(self.engine) as session:
            submission_count = session.exec(
                select(sqlalchemy.func.count(Submission.id))
            ).one()

            submissions = session.exec(
                select(Submission).offset(offset).limit(limit).order_by(order(sort))
            ).all()

            response.headers["X-Limit"] = str(limit)
            response.headers["X-Offset"] = str(offset)
            response.headers["X-Count"] = str(submission_count)

            return submissions

    def create_submission(self, submission: Submission):
        with Session(self.engine) as session:
            session.add(submission)
            session.commit()
            session.refresh(submission)
            return submission

    def update_submission_by_submission_id(
        self, submission_id: str, submission: Submission
    ):
        with Session(self.engine) as session:
            statement = select(Submission).where(
                Submission.submission_id == (submission_id)
            )
            result: Submission = session.exec(statement).one()
            result.score = submission.score
            session.add(result)
            session.commit()
            session.refresh(result)

    def update_submission(self, id: int, submission: Submission):
        with Session(self.engine) as session:
            db_submission = session.get(Submission, id)
            if not db_submission:
                raise HTTPException(status_code=404, detail="Submission not found")
            submission_data = submission.model_dump(exclude_unset=True)
            for key, value in submission_data.items():
                setattr(db_submission, key, value)
            session.add(db_submission)
            session.commit()
            session.refresh(db_submission)
            return db_submission

    def fuzzy_search(
        self,
        query: str = Query(default="query", max_length=50),
        limit: int = Query(default=10, le=100),
    ) -> List[Submission]:
        if len(query) == 0:
            return []

        with Session(self.engine) as session:
            submissions = session.exec(select(Submission)).all()
            choices = [
                {"id": submission.id, "title": submission.title}
                for submission in submissions
            ]

            results = process.extract(query, choices, limit=limit)

            ids = [result[0]["id"] for result in results]

            matched_submissions = [self.read_submission(id) for id in ids]

            return matched_submissions

    def search_submission(
        self,
        submission_id: str = None,
        start_utc: str = Query(alias="startUTC", default=None),
        end_utc: str = Query(alias="endUTC", default=None),
        sort_by: _SubmissionSortBy = Query(
            alias="sortBy", default=_SubmissionSortBy.id
        ),
        order_by: _OrderBy = Query(alias="orderBy", default=_OrderBy.desc),
        offset: int = 0,
        limit: int = Query(default=10, le=100),
    ) -> List[Submission]:
        match sort_by:
            case "id":
                sort = Submission.id
            case "title":
                sort = Submission.title
            case "score":
                sort = Submission.score
            case _:
                sort = Submission.created_utc

        match order_by:
            case "desc":
                order = desc
            case "asc":
                order = asc
            case _:
                order = desc

        with Session(self.engine) as session:
            if submission_id is not None:
                statement = (
                    select(Submission)
                    .where(Submission.submission_id == (submission_id))
                    .offset(offset)
                    .limit(limit)
                )
                results = session.exec(statement).all()

                return results

            if start_utc and end_utc is not None:
                statement = (
                    select(Submission)
                    .where(Submission.created_utc >= start_utc)
                    .where(Submission.created_utc <= end_utc)
                    .order_by(order(sort))
                    .offset(offset)
                    .limit(limit)
                )
                results = session.exec(statement).all()
                return results
            return []

    class _MonthSelection(str, Enum):
        January = "January"
        February = "February"
        March = "March"
        April = "April"
        May = "May"
        Jun = "Jun"
        July = "July"
        August = "August"
        September = "September"
        October = "October"
        November = "November"
        December = "December"
        allMonths = "allMonths"

    class _CountTypeSelection(str, Enum):
        yta = "yta"
        nta = "nta"
        esh = "esh"
        info = "info"
        nah = "nah"

    class _YearSelection(str, Enum):
        year_2022 = "2022"
        year_2023 = "2023"
        year_2024 = "2024"

    # Raw SQL Alchemy Query for this. This will deprecate the use of the top.json static implementation
    # This query could be rewritten to be more database agnostic.
    def top_submission(
        self, year: _YearSelection, month: _MonthSelection, type: _CountTypeSelection
    ) -> List[Submission]:
        match month:
            case "January":
                selectedMonth = "01"
            case "February":
                selectedMonth = "02"
            case "March":
                selectedMonth = "03"
            case "April":
                selectedMonth = "04"
            case "May":
                selectedMonth = "05"
            case "Jun":
                selectedMonth = "06"
            case "July":
                selectedMonth = "07"
            case "August":
                selectedMonth = "08"
            case "September":
                selectedMonth = "09"
            case "October":
                selectedMonth = "10"
            case "November":
                selectedMonth = "11"
            case "December":
                selectedMonth = "12"
            case "allMonths":
                selectedMonth = "allMonths"
            case _:
                selectedMonth = "01"

        with Session(self.engine) as session:
            if selectedMonth == "allMonths":
                statement = """
                    SELECT s.id, s.submission_id, s.title, s.selftext, s.created_utc, s.permalink, s.score FROM (
                    SELECT s.id, s.submission_id, s.title, s.selftext, s.created_utc, s.permalink, s.score,
                    strftime('%Y',DATETIME(ROUND(created_utc), 'unixepoch')) AS sub_year,
                    MAX({type}) AS {type}
                    FROM submission s
                    INNER JOIN breakdown ON s.id = breakdown.id
                    WHERE sub_year = "{year}"
                    GROUP BY sub_year
                    ORDER BY sub_year) s
                """.format(
                    year=year, type=type
                )
            else:
                statement = """
                    SELECT s.id, s.submission_id, s.title, s.selftext, s.created_utc, s.permalink, s.score FROM (
                    SELECT s.id, s.submission_id, s.title, s.selftext, s.created_utc, s.permalink, s.score,
                    strftime('%m',DATETIME(ROUND(created_utc), 'unixepoch')) AS sub_month,
                    strftime('%Y',DATETIME(ROUND(created_utc), 'unixepoch')) AS sub_year,
                    MAX({type}) AS {type}
                    FROM submission s
                    INNER JOIN breakdown ON s.id = breakdown.id
                    WHERE sub_year = "{year}"
                    AND sub_month = "{month}"
                    GROUP BY sub_month, sub_year
                    ORDER BY sub_month, sub_year) s
                """.format(
                    year=year, month=selectedMonth, type=type
                )

            sqlText = sqlalchemy.sql.text(statement)

            resultSet = session.exec(sqlText).all()

            results = []

            for record in resultSet:
                res = dict()
                res["id"] = record[0]
                res["submission_id"] = record[1]
                res["title"] = record[2]
                res["selftext"] = record[3]
                res["created_utc"] = record[4]
                res["permalink"] = record[5]
                res["score"] = record[6]
                results.append(res)

            return results

    def random_submission(self) -> Submission:
        with Session(self.engine) as session:
            count = session.exec(select(sqlalchemy.func.count(Submission.id))).one()

            rand_number = randrange(count)

            submission = self.read_submission(rand_number)

            return submission

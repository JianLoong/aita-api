from enum import Enum
import logging
import os
from random import randrange
from typing import List

from dotenv import dotenv_values
from fastapi import APIRouter, HTTPException, Query
import sqlalchemy
from sqlmodel import Session, SQLModel, asc, create_engine, desc, select

from models.submission import Submission


class SubmissionAPI:
    def __init__(self):
        logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

        self._configure_database()
        self._create_db_and_tables()
        self.router = APIRouter()

        self._setup_submission_routes()

    def _create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def _configure_database(self):
        config = dotenv_values(".env")
        self.sqlite_file_name = config.get("DATABASE_NAME")
        self.sqlite_url = f"sqlite:///database//{self.sqlite_file_name}"
        self.engine = create_engine(self.sqlite_url, echo=False)

    # Routes for submission
    def _setup_submission_routes(self) -> None:
        self.router.add_api_route(
            "/submissions",
            self.read_submissions,
            methods=["GET"],
            tags=["Submission"],
            description="Gets submissions from the database",
        )
        self.router.add_api_route(
            "/submission/{id}",
            self.read_submission,
            methods=["GET"],
            tags=["Submission"],
        )
        # self.router.add_api_route(
        #     "/submission/", self.create_submission, methods=["POST"]
        # )
        # self.router.add_api_route(
        #     "/submission/{id}", self.update_submission, methods=["PATCH"]
        # )
        self.router.add_api_route(
            "/submisssion/search",
            self.search_submission,
            methods=["GET"],
            tags=["Submission"],
        )

        self.router.add_api_route(
            "/top",
            self.top,
            methods=["GET"],
            tags=["Submission"],
            description="The top submission for each count of YTA, NTA and etc",
        )

        self.router.add_api_route(
            "/random",
            self.random,
            methods=["GET"],
            tags=["Submission"],
            description="Obtains a random submission",
        )

    def read_submission(self, id: int):
        with Session(self.engine) as session:
            submission = session.get(Submission, id)
            if not submission:
                raise HTTPException(status_code=404, detail="Submission not found")
            return submission

    class SubmissionSortBy(str, Enum):
        id = "id"
        score = "score"
        title = "title"
        created_utc = "new"

    class OrderBy(str, Enum):
        asc = ("asc",)
        desc = "desc"

    def read_submissions(
        self,
        offset: int = 0,
        limit: int = Query(default=10, le=100),
        sort_by: SubmissionSortBy = Query(alias="sortBy", default=SubmissionSortBy.id),
        order_by: OrderBy = Query(alias="orderBy", default=OrderBy.desc),
    ) -> List[Submission]:
        """
        Read Submissions
        ----------------

        Reads the submissions in the database.

        Parameters:
        ------------
        offset (int):
            The offset
        limit (int):
            The limit
        sort_by (SubmissionSortBy or str):
            The sort by

        Returns:
        --------
        List[Submission]:
            Returns a list of submission. An empty list would  be returned if no results are found.

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
            submissions = session.exec(
                select(Submission).offset(offset).limit(limit).order_by(order(sort))
            ).all()
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

    def search_submission(
        self,
        submission_id: str = None,
        start_utc: str = Query(alias="startUTC", default=None),
        end_utc: str = Query(alias="endUTC", default=None),
        sort_by: SubmissionSortBy = Query(alias="sortBy", default=SubmissionSortBy.id),
        order_by: OrderBy = Query(alias="orderBy", default=OrderBy.desc),
        offset: int = 0,
        limit: int = Query(default=10, le=100),
    ):
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
                statement = select(Submission).where(
                    Submission.submission_id == (submission_id)
                )
                results = session.exec(statement).one()
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

    class MonthSelection(str, Enum):
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
        AllTime = "allMonths"

    class CountTypeSelection(str, Enum):
        yta = "yta"
        nta = "nta"
        esh = "esh"
        info = "info"
        nah = "nah"

    class YearSelection(str, Enum):
        year_2022 = "2022"
        year_2023 = "2023"
        year_2024 = "2024"

    # Raw SQL Alchemy Query for this. This will deprecate the use of the top.json static implementation
    # This query could be rewritten to be more database agnostic.
    def top(self, year: YearSelection, month: MonthSelection, type: CountTypeSelection):
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
                    SELECT s.id, s.submission_id, s.title, s.selftext, s.created_utc, s.permalink, s.score, strftime('%m',DATETIME(ROUND(created_utc), 'unixepoch')) AS sub_month,
                    strftime('%Y',DATETIME(ROUND(created_utc), 'unixepoch')) AS sub_year,
                    MAX({type}) AS {type}
                    FROM submission s
                    INNER JOIN breakdown ON s.id = breakdown.id
                    WHERE sub_year = "{year}"
                    GROUP BY sub_year
                    ORDER BY sub_year
                """.format(
                    year=year, type=type
                )
            else:
                statement = """
                    SELECT s.id, s.submission_id, s.title, s.selftext, s.created_utc, s.permalink, s.score, strftime('%m',DATETIME(ROUND(created_utc), 'unixepoch')) AS sub_month,
                    strftime('%Y',DATETIME(ROUND(created_utc), 'unixepoch')) AS sub_year,
                    MAX({type}) AS {type}
                    FROM submission s
                    INNER JOIN breakdown ON s.id = breakdown.id
                    WHERE sub_year = "{year}"
                    AND sub_month = "{month}"
                    GROUP BY sub_month, sub_year
                    ORDER BY sub_month, sub_year
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
                res["month"] = record[7]
                res["year"] = record[8]
                res["count"] = record[9]
                results.append(res)

            return results

    def random(self):
        with Session(self.engine) as session:
            count = session.exec(select(sqlalchemy.func.count(Submission.id))).one()

            rand_number = randrange(count)

            submission = self.read_submission(rand_number)

            return submission

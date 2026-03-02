import logging
import re
from enum import Enum
from random import randrange
from typing import List

import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import Engine
from sqlmodel import Session, asc, desc, select

from aita_api.models.message import Message
from aita_api.models.submission import Submission

logger = logging.getLogger(__name__)


class SubmissionAPI:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.router = APIRouter()

        self._setup_submission_routes()

    # Routes for submission
    def _setup_submission_routes(self) -> None:
        oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

        self.router.add_api_route(
            "/submissions",
            self.create_submission,
            methods=["POST"],
            tags=["Submission"],
            description="Creates a submission",
            dependencies=[Depends(oauth2_scheme)],
            responses={
                status.HTTP_401_UNAUTHORIZED: {"model": Message},
                status.HTTP_409_CONFLICT: {"model": Message},
            },
        )

        self.router.add_api_route(
            "/submissions/{id}",
            self.update_submission,
            methods=["PATCH"],
            tags=["Submission"],
            description="Updates a submission",
            dependencies=[Depends(oauth2_scheme)],
            responses={status.HTTP_401_UNAUTHORIZED: {"model": Message}},
        )

        self.router.add_api_route(
            "/submissions/{id}",
            self.upsert_submission,
            methods=["PUT"],
            tags=["Submission"],
            description="Upserts a submission",
            dependencies=[Depends(oauth2_scheme)],
            responses={status.HTTP_401_UNAUTHORIZED: {"model": Message}},
        )

        self.router.add_api_route(
            "/submissions/{id}",
            self.delete_submission,
            methods=["DELETE"],
            tags=["Submission"],
            description="Deletes a submission",
            dependencies=[Depends(oauth2_scheme)],
            responses={
                status.HTTP_200_OK: {"model": Message},
                status.HTTP_401_UNAUTHORIZED: {"model": Message},
            },
        )

        self.router.add_api_route(
            "/submissions",
            self.read_submissions,
            methods=["GET"],
            tags=["Submission"],
            description="Gets submissions from the database",
            responses={status.HTTP_404_NOT_FOUND: {"model": Message}},
        )
        self.router.add_api_route(
            "/submission/{id}",
            self.read_submission,
            methods=["GET"],
            tags=["Submission"],
            description="Gets submission from database based on id",
            responses={status.HTTP_404_NOT_FOUND: {"model": Message}},
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
            responses={
                404: {
                    "details": "Submission not found",
                    "content": {
                        "application/json": {
                            "example": {"details": "Submission not found"},
                        }
                    },
                }
            },
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
        try:
            with Session(self.engine) as session:
                submission = session.get(Submission, id)
                if not submission:
                    raise HTTPException(status_code=404, detail="Submission not found")
                return submission
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in read_submission for id {id}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    def read_submissions(
        self,
        request: Request,
        response: Response,
        offset: int = Query(default=0, le=100),
        limit: int = Query(default=10, le=100),
        sort_by: _SubmissionSortBy = Query(alias="sortBy", default=_SubmissionSortBy.id),
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
        try:
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
                submission_count = session.exec(select(sqlalchemy.func.count(Submission.id))).one()

                submissions = session.exec(
                    select(Submission).offset(offset).limit(limit).order_by(order(sort))
                ).all()

                response.headers["X-Limit"] = str(limit)
                response.headers["X-Offset"] = str(offset)
                response.headers["X-Count"] = str(submission_count)

                return submissions
        except Exception as e:
            logger.error(f"Error in read_submissions: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    def create_submission(self, submission: Submission) -> Submission:
        try:
            with Session(self.engine) as session:
                session.add(submission)
                session.commit()
                session.refresh(submission)
                return submission
        except Exception as e:
            logger.error(f"Error in create_submission: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to create submission: {str(e)}")

    def update_submission_by_submission_id(
        self, submission_id: str, submission: Submission
    ) -> Submission:
        with Session(self.engine) as session:
            statement = select(Submission).where(Submission.submission_id == (submission_id))
            result: Submission = session.exec(statement).one()
            result.score = submission.score
            session.add(result)
            session.commit()
            session.refresh(result)

            return result

    def update_submission(self, id: int, submission: Submission) -> Submission:
        try:
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
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in update_submission for id {id}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to update submission: {str(e)}")

    def fuzzy_search(
        self,
        query: str = Query(default="query", max_length=50),
        limit: int = Query(default=20, le=100),
    ) -> List[Submission]:
        if len(query) == 0:
            return []

        cleaned_query = re.sub("\\W+", "", query)

        try:
            with Session(self.engine) as session:
                statement = sqlalchemy.sql.text(
                    """
                    SELECT id FROM submission_fts 
                    WHERE submission_fts MATCH :query 
                    ORDER BY RANK 
                    LIMIT :limit
                """
                )
                bound_statement = statement.bindparams(query=cleaned_query, limit=limit)

                resultSet = session.exec(bound_statement).all()

                results = []

                for record in resultSet:
                    res = dict()
                    res["id"] = record[0]
                    results.append(res)

                ids = [result["id"] for result in results]

                if not ids:
                    return []

                matched_submissions = session.exec(
                    select(Submission).where(Submission.id.in_(ids))
                ).all()

                return matched_submissions

        except Exception as e:
            logger.error(f"Error in fuzzy_search with query '{query}': {str(e)}", exc_info=True)
            return []

    def search_submission(
        self,
        response: Response = Response(),
        submission_id: str = None,
        start_utc: float = Query(alias="startUTC", default=None),
        end_utc: float = Query(alias="endUTC", default=None),
        sort_by: _SubmissionSortBy = Query(alias="sortBy", default=_SubmissionSortBy.id),
        order_by: _OrderBy = Query(alias="orderBy", default=_OrderBy.desc),
        offset: int = 0,
        limit: int = Query(default=10, le=100),
    ) -> List[Submission]:
        try:
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

            response.headers["X-Limit"] = str(limit)
            response.headers["X-Offset"] = str(offset)

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
        except Exception as e:
            logger.error(f"Error in search_submission: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

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
        year_2025 = "2025"
        year_2026 = "2026"

    # Raw SQL Alchemy Query for this. This will deprecate the use of the top.json static implementation
    # This query could be rewritten to be more database agnostic.
    def top_submission(
        self, year: _YearSelection, month: _MonthSelection, type: _CountTypeSelection
    ) -> List[Submission]:
        try:
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

            # Extract string values from enums
            type_value = type.value if hasattr(type, "value") else str(type)
            year_value = year.value if hasattr(year, "value") else str(year)

            # Validate type to prevent SQL injection since column names can't be parameterized
            valid_types = {"yta", "nta", "esh", "info", "nah"}
            if type_value not in valid_types:
                raise HTTPException(status_code=400, detail="Invalid type parameter")

            with Session(self.engine) as session:
                if selectedMonth == "allMonths":
                    statement = sqlalchemy.sql.text(
                        f"""
                        SELECT s.id, s.submission_id, s.title, s.selftext, s.created_utc, s.permalink, s.score,
                        strftime('%Y', DATETIME(ROUND(s.created_utc), 'unixepoch')) AS sub_year,
                        MAX(b.{type_value}) AS max_count
                        FROM submission s
                        INNER JOIN breakdown b ON s.id = b.id
                        WHERE strftime('%Y', DATETIME(ROUND(s.created_utc), 'unixepoch')) = :year
                        GROUP BY sub_year
                        ORDER BY max_count DESC
                    """
                    )
                    bound_statement = statement.bindparams(year=year_value)
                else:
                    statement = sqlalchemy.sql.text(
                        f"""
                        SELECT s.id, s.submission_id, s.title, s.selftext, s.created_utc, s.permalink, s.score,
                        strftime('%m', DATETIME(ROUND(s.created_utc), 'unixepoch')) AS sub_month,
                        strftime('%Y', DATETIME(ROUND(s.created_utc), 'unixepoch')) AS sub_year,
                        MAX(b.{type_value}) AS max_count
                        FROM submission s
                        INNER JOIN breakdown b ON s.id = b.id
                        WHERE strftime('%Y', DATETIME(ROUND(s.created_utc), 'unixepoch')) = :year
                        AND strftime('%m', DATETIME(ROUND(s.created_utc), 'unixepoch')) = :month
                        GROUP BY sub_month, sub_year
                        ORDER BY max_count DESC
                    """
                    )
                    bound_statement = statement.bindparams(year=year_value, month=selectedMonth)

                logger.info(
                    f"Executing top_submission query: year={year_value}, month={selectedMonth}, type={type_value}"
                )
                resultSet = session.exec(bound_statement).all()

                results = []
                for record in resultSet:
                    res = {
                        "id": record[0],
                        "submission_id": record[1],
                        "title": record[2],
                        "selftext": record[3],
                        "created_utc": record[4],
                        "permalink": record[5],
                        "score": record[6],
                    }
                    results.append(res)

                logger.info(f"top_submission returned {len(results)} results")
                return results
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Error in top_submission (year={year}, month={month}, type={type}): {str(e)}",
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")

    def upsert_submission(self, id: int, submission: Submission) -> Submission:
        with Session(self.engine) as session:
            db_submission = session.get(Submission, id)
            if not db_submission:
                session.add(submission)
                session.commit()
                session.refresh(submission)
                return submission
            else:
                submission_data = submission.model_dump(exclude_unset=True)
                for key, value in submission_data.items():
                    setattr(db_submission, key, value)
                session.add(db_submission)
                session.commit()
                session.refresh(db_submission)
                return db_submission

    def random_submission(self) -> Submission:
        try:
            with Session(self.engine) as session:
                count = session.exec(select(sqlalchemy.func.count(Submission.id))).one()

                if count == 0:
                    raise HTTPException(status_code=404, detail="Submission not found")

                rand_number = randrange(count)

                submission = self.read_submission(rand_number)

                return submission
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in random_submission: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Failed to get random submission: {str(e)}"
            )

    def delete_submission(self, id: int):
        try:
            with Session(self.engine) as session:
                submission = session.get(Submission, id)
                if not submission:
                    raise HTTPException(status_code=404, detail="Submission not found")
                session.delete(submission)
                session.commit()

                return {"ok": True}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in delete_submission for id {id}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to delete submission: {str(e)}")

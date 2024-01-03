import json
import logging
import os

import sqlalchemy
from fastapi import APIRouter, HTTPException, Query
from sqlmodel import Session, SQLModel, create_engine, desc, select

from models.breakdown import Breakdown
from models.comment import Comment
from models.submission import Submission
from models.summary import Summary


class API:
    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def configure_database(self):
        self.sqlite_file_name = "AmItheAsshole.db"
        self.sqlite_url = f"sqlite:///database//{self.sqlite_file_name}"

        self.engine = create_engine(self.sqlite_url, echo=False)

    # Routes for submission
    def setup_submission_routes(self):
        self.router.add_api_route(
            "/submissions", self.read_submissions, methods=["GET"]
        )
        self.router.add_api_route(
            "/submission/{id}", self.read_submission, methods=["GET"]
        )
        # self.router.add_api_route(
        #     "/submission/", self.create_submission, methods=["POST"]
        # )

        # self.router.add_api_route(
        #     "/submission/{id}", self.update_submission, methods=["PATCH"]
        # )

        self.router.add_api_route(
            "/search_submission", self.search_submission, methods=["GET"]
        )

    def __init__(self):
        logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

        self.configure_database()
        self.create_db_and_tables()
        self.router = APIRouter()

        # self.router.add_api_route("/indexes", self.read_indexes, methods=["GET"])

        self.router.add_api_route("/search", self.read_search, methods=["GET"])

        self.router.add_api_route("/top", self.read_top, methods=["GET"])

        self.router.add_api_route("/test_top", self.top, methods=["GET"])

        self.setup_submission_routes()

        # self.router.add_api_route(
        #     "/search_comment", self.search_comments, methods=["GET"]
        # )

        # self.router.add_api_route("/comment/{id}", self.read_comment, methods=["GET"])
        self.router.add_api_route("/summary/{id}", self.read_summary, methods=["GET"])

    def read_submissions(
        self, offset: int = 0, limit: int = Query(default=100, le=100)
    ):
        with Session(self.engine) as session:
            submissions = session.exec(
                select(Submission)
                .offset(offset)
                .limit(limit)
                .order_by(desc(Submission.created_utc))
            ).all()
            return submissions

    def read_submission(self, id: int):
        with Session(self.engine) as session:
            submission = session.get(Submission, id)
            if not submission:
                raise HTTPException(status_code=404, detail="Submission not found")
            return submission

    def create_breakdown(self, breakdown: Breakdown):
        with Session(self.engine) as session:
            session.add(breakdown)
            session.commit()
            session.refresh(breakdown)
            return breakdown

    def create_submission(self, submission: Submission):
        with Session(self.engine) as session:
            submission.id = None
            session.add(submission)
            session.commit()
            session.refresh(submission)
            return submission

    def create_comment(self, comment: Comment):
        with Session(self.engine) as session:
            comment.id = None
            session.add(comment)
            session.commit()
            session.refresh(comment)
            return comment

    def read_indexes(self):
        indexes = []
        with Session(self.engine) as session:
            statement = select(Submission)
            results = session.exec(statement)
            for submission in results:
                entry = dict()
                entry["id"] = submission.id
                entry["scores"] = submission.score
                entry["created_utc"] = submission.created_utc
                indexes.append(entry)

        return indexes

    def read_top(self):
        with open(".//endpoints//static//top.json") as json_file:
            data = json.load(json_file)

            return data

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

    # Raw SQL Alchemy Query for this. This will deprecate the use of the top.json static implementation
    # This query could be rewritten to be more database agnostic.
    def top(self, year: str, month: str, type: str):
        with Session(self.engine) as session:
            statement = """
                SELECT s.id, s.submission_id, s.title, s.selftext, s.created_utc, s.permalink, s.score, strftime('%m',DATETIME(ROUND(created_utc), 'unixepoch')) AS sub_month,       strftime('%Y',DATETIME(ROUND(created_utc), 'unixepoch')) AS sub_year,
                MAX({type}) AS "{type}"
                FROM submission s
                INNER JOIN breakdown ON s.id = breakdown.id
                WHERE sub_year = "{year}"
                AND sub_month = "{month}"
                GROUP BY sub_month, sub_year
                ORDER BY sub_month, sub_year
            """.format(
                year=year, month=month, type=type
            )

            sqlText = sqlalchemy.sql.text(statement)

            resultSet = session.exec(sqlText).all()

            results = []

            for record in resultSet:
                res = dict()
                print("\n", record)
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

    def search_comments(
        self,
        submission_id: str = None,
        start_utc: int = None,
        end_utc: int = None,
        order_by: str = None,
        offset: int = 0,
        limit: int = Query(default=50000, le=50000),
    ):
        with Session(self.engine) as session:
            if submission_id is not None:
                statement = select(Comment).where(
                    Comment.submission_id == (submission_id)
                )
                results = session.exec(statement).all()
                return results
            # 1664646465
            # 1701692714000

            if start_utc is not None:
                statement = (
                    select(Comment)
                    .where(Comment.created_utc >= start_utc)
                    .where(Comment.created_utc <= end_utc)
                    .order_by(Comment.score)
                    .offset(offset)
                    .limit(limit)
                )
                results = session.exec(statement).all()
                return results

            return []

    def search_submission(
        self,
        submission_id: str = None,
        start_utc: int = None,
        end_utc: int = None,
        offset: int = 0,
        limit: int = Query(default=100, le=50000),
    ):
        with Session(self.engine) as session:
            if submission_id is not None:
                statement = select(Submission).where(
                    Submission.submission_id == (submission_id)
                )
                results = session.exec(statement).one()
                return results
            # 1664646465
            # 1701692714000

            if start_utc is not None:
                statement = (
                    select(Submission)
                    .where(Submission.created_utc >= start_utc)
                    .where(Submission.created_utc <= end_utc)
                    .order_by(desc(Submission.score))
                    .offset(offset)
                    .limit(limit)
                )
                results = session.exec(statement).all()
                return results

            return []

    def read_comment(self, id: int):
        with Session(self.engine) as session:
            comment = session.get(Comment, id)
            if not comment:
                raise HTTPException(status_code=404, detail="Comment not found")
            return comment

    def read_search(self):
        with open(".//endpoints//static//search.json") as json_file:
            data = json.load(json_file)

            return data

    def create_summary(self, summary: Summary):
        with Session(self.engine) as session:
            session.add(summary)
            session.commit()
            session.refresh(summary)
            return summary

    def read_summary(self, id: int):
        with Session(self.engine) as session:
            summary = session.get(Summary, id)
            if not summary:
                raise HTTPException(status_code=404, detail="Summary not found")
            return summary

    def update_summary(self, id: int, summary: Summary):
        with Session(self.engine) as session:
            db_summary = session.get(Summary, id)
            if not db_summary:
                raise HTTPException(status_code=404, detail="Submission not found")
            summary_data = summary.model_dump(exclude_unset=True)
            for key, value in summary_data.items():
                setattr(db_summary, key, value)
            session.add(db_summary)
            session.commit()
            session.refresh(db_summary)
            return db_summary

import os

import asyncpraw
from asyncpraw.models import MoreComments
from dotenv import find_dotenv, load_dotenv
from fastapi import Response

from endpoints.comment_api import CommentAPI
from endpoints.database_config import DatabaseConfig
from endpoints.submission_api import SubmissionAPI
from models.comment import Comment
from models.submission import Submission


class Crawler:
    _instance = None
    _verbose = False

    def _configure_agent(self) -> None:
        self.agent = "Mozilla/5.0 (platform; rv:geckoversion) Gecko/geckotrail Firefox/firefoxversion"

        load_dotenv(find_dotenv())

        self.client_id = os.environ.get("REDDIT_CLIENT_ID")
        self.client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
        self.subreddit_name = os.environ.get("SUBREDDIT_NAME")
        self.post_limit: int = int(os.environ.get("POST_LIMIT"))

    def _validate_configuration(self) -> bool:
        if self.client_id is None or self.client_secret is None:
            return False
        if self.subreddit_name is None:
            return False

    def __new__(cls, verbose: bool = False):
        if cls._instance is None:
            cls._instance = super(Crawler, cls).__new__(cls)
            cls._instance._configure_agent()
            cls._instance._verbose = verbose

        return cls._instance

    async def process(self) -> None:
        async with asyncpraw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.agent,
        ) as reddit:
            reddit.read_only = True

            db_config = DatabaseConfig()

            engine = db_config.get_engine()

            submission_api = SubmissionAPI(engine)
            comment_api = CommentAPI(engine)

            self._verbose is True and print("Creating/Updating submission")

            subreddit = await reddit.subreddit(self.subreddit_name, fetch=True)

            async for submission in subreddit.hot(limit=self.post_limit):
                custom_submission: Submission = Submission()

                custom_submission.id = None
                custom_submission.submission_id = submission.id
                custom_submission.selftext = submission.selftext
                custom_submission.title = submission.title
                custom_submission.created_utc = submission.created_utc
                custom_submission.permalink = submission.permalink
                custom_submission.score = submission.score

                if submission.selftext == "[removed]":
                    continue

                response = Response()

                try:
                    results = submission_api.search_submission(
                        response=response,
                        submission_id=custom_submission.submission_id,
                        limit=1,
                    )

                    if len(results) == 0:
                        self._verbose is True and print(
                            f"Creating submission for {custom_submission.title}"
                        )
                        submission_api.create_submission(custom_submission)
                    else:
                        custom_submission.id = results[0].id
                        self._verbose is True and print(
                            f"Updating submission for {results[0].id} {custom_submission.title}"
                        )
                        submission_api.update_submission(
                            results[0].id, custom_submission
                        )

                    comments = await submission.comments()
                    await comments.replace_more(limit=0)
                    all_comments = await comments.list()

                    for comment in all_comments:
                        if isinstance(comment, MoreComments):
                            continue

                        custom_comment: Comment = Comment()
                        custom_comment.submission_id = submission.id
                        custom_comment.message = comment.body
                        custom_comment.parent_id = comment.parent_id
                        custom_comment.created_utc = comment.created_utc
                        custom_comment.score = comment.score
                        custom_comment.comment_id = comment.id

                        results = comment_api.search_comments(
                            comment_id=custom_comment.comment_id
                        )

                        if len(results) == 0:
                            comment_api.create_comment(custom_comment)

                except Exception as error:
                    self._verbose is True and print(error)

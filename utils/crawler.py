import praw
import sqlalchemy
import logging
import os
from endpoints.comment_api import CommentAPI
from endpoints.database_config import DatabaseConfig
from endpoints.submission_api import SubmissionAPI
from models.comment import Comment
from models.submission import Submission
from dotenv import find_dotenv, load_dotenv


class Crawler:
    def configure_agent(self) -> None:
        self.agent = "Mozilla/5.0 (platform; rv:geckoversion) Gecko/geckotrail Firefox/firefoxversion"

        load_dotenv(find_dotenv())

        self.client_id = os.environ.get("REDDIT_CLIENT_ID")
        self.client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
        self.subreddit_name = os.environ.get("SUBREDDIT_NAME")
        self.post_limit: int = int(os.environ.get("POST_LIMIT"))

    def validate_configuration(self) -> bool:
        if self.client_id is None or self.client_secret is None:
            return False
        if self.subreddit_name is None:
            return False

    def crawl(self) -> None:
        reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.agent,
        )

        db_config = DatabaseConfig()

        engine = db_config.get_engine()

        submission_api = SubmissionAPI(engine)
        comment_api = CommentAPI(engine)

        for submission in reddit.subreddit(self.subreddit_name).hot(
            limit=self.post_limit
        ):
            custom_submission: Submission = Submission()

            custom_submission.id = None
            custom_submission.submission_id = submission.id
            custom_submission.selftext = submission.selftext
            custom_submission.title = submission.title
            custom_submission.created_utc = submission.created_utc
            custom_submission.permalink = submission.permalink
            custom_submission.score = submission.score

            try:
                if submission.selftext == "[removed]":
                    continue
                # logging.info("Creating submission for " + submission.title)
                print("Creating submission for " + submission.title)
                submission_api.create_submission(custom_submission)
            except sqlalchemy.exc.IntegrityError:
                submission_api.update_submission_by_submission_id(
                    submission.id, custom_submission
                )

            submission.comments.replace_more(limit=0)
            comments = submission.comments.list()

            for comment in comments:
                custom_comment: Comment = Comment()
                custom_comment.submission_id = submission.id
                custom_comment.message = comment.body
                custom_comment.parent_id = comment.parent_id
                custom_comment.created_utc = comment.created_utc
                custom_comment.score = comment.score
                custom_comment.comment_id = comment.id

                try:
                    comment_api.create_comment(custom_comment)
                except sqlalchemy.exc.IntegrityError:
                    continue


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

    crawler = Crawler()

    crawler.configure_agent()

    if crawler.validate_configuration is False:
        raise Exception("Invalid configuration.")

    crawler.crawl()
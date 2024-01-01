import praw
from dotenv import dotenv_values
import sqlalchemy
from models.comment import Comment
from models.submission import Submission
from endpoints.api import API

subreddit_name = "AmItheAsshole"
reddit = None
UPDATE = True
POST_LIMIT = 50

reddit: praw.Reddit = None

agent = (
    "Mozilla/5.0 (platform; rv:geckoversion) Gecko/geckotrail Firefox/firefoxversion"
)

config = dotenv_values(".env")
client_id = config.get("client_id")
client_secret = config.get("client_secret")

if client_id is None or client_secret is None:
    exit(1)

reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=agent)

api = API()

for submission in reddit.subreddit(subreddit_name).hot(limit=POST_LIMIT):
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
        api.create_submission(custom_submission)
    except sqlalchemy.exc.IntegrityError:
        api.update_submission_by_submission_id(submission.id, custom_submission)

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
            api.create_comment(custom_comment)
        except sqlalchemy.exc.IntegrityError:
            continue

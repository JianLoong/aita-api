import praw
from dotenv import dotenv_values
from models.submission import Submission
from end_points.api import API

subreddit_name = "AmItheAsshole"
reddit = None
UPDATE = True
POST_LIMIT = 1

reddit: praw.Reddit = None

agent = "Mozilla/5.0 (platform; rv:geckoversion) Gecko/geckotrail Firefox/firefoxversion"

config = dotenv_values(".env")
client_id = config.get("client_id")
client_secret = config.get("client_secret")

if client_id is None or client_secret is None:
    exit(1)

reddit = praw.Reddit(
    client_id=client_id,
    client_secret=client_secret,
    user_agent=agent
)

api = API()

for submission in reddit.subreddit(subreddit_name).hot(limit=POST_LIMIT):
    custom_submission: Submission = Submission()
    print(submission.id)
    print(submission.selftext)
    print(submission.title)
    print(submission.created_utc)
    print(submission.permalink)
    print(submission.score) 
    api.create_submission(custom_submission)
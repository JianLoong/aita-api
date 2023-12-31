import praw
from dotenv import dotenv_values

# subreddit_name = "AmItheAsshole"
subreddit_name = "programming"
reddit = None
UPDATE = True
POST_LIMIT = 50

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

for submission in reddit.subreddit(subreddit_name).hot(limit=POST_LIMIT):
    print(submission.selftext)

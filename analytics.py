# Perform sentiment analysis and then create JSON files that will be used for application
import calendar
import re
from datetime import datetime, timedelta

from afinn import Afinn
from nltk.probability import FreqDist
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nrclex import NRCLex

from endpoints.api import API


def process(submissions):
    afinn = Afinn()

    for submission in submissions:
        result = {"id": 0, "afinn": 0, "emotion": 0, "word_freq": 0, "counts": 0}

        replies = ""
        for reply in submission["replies"]:
            replies = replies + reply

        result["id"] = submission["id"]
        # result["afinn"] = afinn.score(replies)
        # result["emotion"] = NRCLex(replies).raw_emotion_scores
        frequencies = word_frequency(replies)
        # result["word_freq"] = frequencies[0]
        result["total"] = len(submission["replies"])
        result["counts"] = frequencies[1]

        print(result)

def get_submissions():
    # This function will make indices in for the API to consume with the submission IDs and the file name is the unix timestamp
    # This does not need to be date aware
    today = datetime.today()
    start = datetime(today.year, today.month, today.day) + timedelta(1)
    yesterday = start - timedelta(2)

    # Convert time to UTC time
    start_utc = calendar.timegm(start.timetuple())
    yesterday_utc = calendar.timegm(yesterday.timetuple())

    api = API()

    submissions = api.search_submission(start_utc=yesterday_utc, end_utc=start_utc)

    submisions_json = []

    for submission in submissions:

        comments = api.search_comments(submission_id=submission.submission_id)
        submission_dict = submission.__dict__

        replies = []
        for reply in comments:
            replies.append(reply.message)
        submission_dict["replies"] = replies

        submisions_json.append(submission_dict)

    return submisions_json


def word_frequency(text):
    text = text.lower().replace(".", " ")
    text = re.sub("\W+", " ", text)
    text = word_tokenize(text)
    text = remove_stop_words(text)

    fdist = FreqDist(text)  # .most_common(10)

    freq = dict(fdist)
    nta_count = 0
    yta_count = 0
    esh_count = 0
    info_count = 0
    nah_count = 0

    if "nta" in freq:
        nta_count = freq["nta"]
    if "yta" in freq:
        yta_count = freq["yta"]
    if "esh" in freq:
        esh_count = freq["esh"]
    if "info" in freq:
        info_count = freq["info"]
    if "nah" in freq:
        nah_count = freq["nah"]

    counts = {
        "nta_count": nta_count,
        "yta_count": yta_count,
        "esh_count": esh_count,
        "info_count": info_count,
        "nah_count": nah_count,
    }

    return [dict(fdist.most_common(30)), counts]


def remove_stop_words(word_tokens):
    stop_words = set(stopwords.words("english"))

    filtered_sentence = [w for w in word_tokens if not w.lower() in stop_words]
    filtered_sentence = []

    for w in word_tokens:
        if w not in stop_words:
            filtered_sentence.append(w)

    return filtered_sentence


if __name__ == "__main__":
    print("Running analytics")
    submissions = get_submissions()
    # print("Processing submissions")
    process(submissions)

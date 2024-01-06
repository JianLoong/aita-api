# Perform sentiment analysis and then create JSON files that will be used for application
import calendar
import json
import logging
import os
import re
from datetime import datetime, timedelta
from dotenv import find_dotenv, load_dotenv

import sqlalchemy
from afinn import Afinn
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.tokenize import word_tokenize
from nrclex import NRCLex
from sqlmodel import Session, create_engine, select
from endpoints.breakdown_api import BreakdownAPI
from endpoints.comment_api import CommentAPI

from endpoints.database_config import DatabaseConfig
from endpoints.submission_api import SubmissionAPI
from endpoints.summary_api import SummaryAPI
from models.breakdown import Breakdown
from models.submission import Submission
from models.summary import Summary


class AnalyticsProcessor:
    def __init__(self):
        engine = DatabaseConfig().get_engine()
        self.submission_api = SubmissionAPI(engine)
        self.summary_api = SummaryAPI(engine)
        self.breakdown_api = BreakdownAPI(engine)
        self.comment_api = CommentAPI(engine)

    def process(self, submissions):
        afinn = Afinn()

        for submission in submissions:
            result = {"id": 0, "afinn": 0, "emotion": 0, "word_freq": 0, "counts": 0}

            replies = ""

            print("Processsing submission : " + submission["title"])
            for reply in submission["replies"]:
                replies = replies + reply

            result["id"] = submission["id"]
            result["afinn"] = afinn.score(replies)
            result["emotion"] = NRCLex(replies).raw_emotion_scores
            frequencies = self.word_frequency(replies)
            result["word_freq"] = frequencies[0]
            result["no_of_replies"] = len(submission["replies"])
            result["counts"] = frequencies[1]

            summary: Summary = Summary()

            summary.id = result["id"]
            summary.afinn = result["afinn"]
            summary.counts = result["counts"]
            summary.emotion = result["emotion"]
            summary.word_freq = result["word_freq"]

            nta_count = summary.counts.get("nta_count")
            yta_count = summary.counts.get("yta_count")
            esh_count = summary.counts.get("esh_count")
            info_count = summary.counts.get("info_count")
            nah_count = summary.counts.get("nah_count")

            breakdown = Breakdown(
                id=result["id"],
                nta=nta_count,
                yta=yta_count,
                esh=esh_count,
                info=info_count,
                nah=nah_count,
            )

            try:
                self.summary_api.create_summary(summary)
            except sqlalchemy.exc.IntegrityError:
                self.summary_api.update_summary(result["id"], summary)

            try:
                self.breakdown_api.create_breakdown(breakdown)
            except sqlalchemy.exc.IntegrityError:
                self.breakdown_api.update_breakdown(breakdown.id, breakdown)
                continue

    def get_submissions(self):
        today = datetime.today()
        start = datetime(today.year, today.month, today.day) + timedelta(1)
        yesterday = start - timedelta(2)

        # Convert time to UTC time
        start_utc = calendar.timegm(start.timetuple())
        yesterday_utc = calendar.timegm(yesterday.timetuple())

        submissions = self.submission_api.search_submission(
            start_utc=yesterday_utc, end_utc=start_utc, limit=100
        )

        submissions_json = []

        logging.info("Total submissions " + str(len(submissions)))

        for submission in submissions:
            comments = self.comment_api.search_comments(
                submission_id=submission.submission_id
            )
            # logging.info("Creating submission for " + submission.title)
            submission_dict = submission.__dict__

            replies = []
            for reply in comments:
                replies.append(reply.message)
            submission_dict["replies"] = replies

            submissions_json.append(submission_dict)

        return submissions_json

    def word_frequency(self, text):
        text = text.lower().replace(".", " ")
        text = re.sub("\\W+", " ", text)
        text = word_tokenize(text)
        text = self.remove_stop_words(text)

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

    def remove_stop_words(self, word_tokens):
        stop_words = set(stopwords.words("english"))

        filtered_sentence = [w for w in word_tokens if not w.lower() in stop_words]
        filtered_sentence = []

        for w in word_tokens:
            if w not in stop_words:
                filtered_sentence.append(w)

        return filtered_sentence

    def generate_search(self):
        indexes = []

        # sqlite_file_name = "AmItheAsshole.db"
        load_dotenv(find_dotenv())
        # config = dotenv_values(".env")
        sqlite_file_name = os.environ.get("DATABASE_NAME")
        sqlite_url = f"sqlite:///database//{sqlite_file_name}"
        engine = create_engine(sqlite_url, echo=False)

        with Session(engine) as session:
            statement = select(Submission)
            results = session.exec(statement)
            for submission in results:
                entry = dict()
                entry["id"] = submission.id
                entry["title"] = submission.title
                entry["created_utc"] = submission.created_utc

                indexes.append(entry)

        self.write_to_file(json.dumps(indexes), "search")

    def write_to_file(self, json, file_name):
        f = open("./endpoints/static/" + str(file_name) + ".json", "w")
        f.write(json)
        f.close()


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

    print("Running analytics")

    ap = AnalyticsProcessor()
    # print("Processing submissions")
    submissions = ap.get_submissions()
    ap.process(submissions)
    ap.generate_search()

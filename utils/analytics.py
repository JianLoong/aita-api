# Perform sentiment analysis and then create JSON files that will be used for application
import calendar
import logging
import re
from datetime import datetime, timedelta

from afinn import Afinn
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.tokenize import word_tokenize
from nrclex import NRCLex

from endpoints.breakdown_api import BreakdownAPI
from endpoints.comment_api import CommentAPI
from endpoints.database_config import DatabaseConfig
from endpoints.submission_api import SubmissionAPI
from endpoints.summary_api import SummaryAPI
from models.breakdown import Breakdown
from models.summary import Summary


class AnalyticsProcessor:
    _instance = None

    def _configure_processor(self):
        self.engine = DatabaseConfig().get_engine()
        self.submission_api = SubmissionAPI(self.engine)
        self.summary_api = SummaryAPI(self.engine)
        self.breakdown_api = BreakdownAPI(self.engine)
        self.comment_api = CommentAPI(self.engine)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AnalyticsProcessor, cls).__new__(cls)
            cls._instance._configure_processor()

        return cls._instance

    def process(self):
        afinn = Afinn()

        submissions = self.get_submissions()

        for submission in submissions:
            result = {"id": 0, "afinn": 0, "emotion": 0, "word_freq": 0, "counts": 0}

            replies = ""

            print(
                f"Creating analysis for {str(submission['id'])} {submission['title']}"
            )

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

            id = result["id"]

            self.summary_api.upsert_summary(id, summary)
            self.breakdown_api.upsert_breakdown(id, breakdown)

    def get_submissions(self):
        today = datetime.today()
        start = datetime(today.year, today.month, today.day) + timedelta(1)
        yesterday = start - timedelta(2)

        # Convert time to UTC time
        start_utc = calendar.timegm(start.timetuple())
        yesterday_utc = calendar.timegm(yesterday.timetuple())

        submissions = self.submission_api.search_submission(
            start_utc=yesterday_utc, end_utc=start_utc, limit=10000
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

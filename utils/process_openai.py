import logging
import os
from fastapi import HTTPException

from dotenv import find_dotenv, load_dotenv
from openai import OpenAI
from endpoints.database_config import DatabaseConfig
from endpoints.openai_inference_api import OpenAIInferenceAPI
from endpoints.submission_api import SubmissionAPI
from models.openai_analytics import OpenAIAnalysis
from utils.analytics import AnalyticsProcessor


class OpenAIProccessor:
    def __init__(self):
        print("Creating")
        load_dotenv(find_dotenv())
        self.api_key = os.environ.get("OPENAI_API_KEY")

        database_config = DatabaseConfig()
        engine = database_config.get_engine()

        self.submission_api = SubmissionAPI(engine)

        self.open_ai_analysis = OpenAIInferenceAPI(engine)

        self.client = OpenAI()

    def process(self, submissions):
        for sub in submissions:
            try:
                self.open_ai_analysis.read_openai_inference(sub["id"])
                logging.info("Analysis exist. Skipping")

            except HTTPException:
                # Doesnt exist so process
                text = self.submission_api.read_submission(sub["id"])
                question = """
                Explain tones of the following narrative in a list format and actions to be taken: {selftext}
                """.format(
                    selftext=text
                )

                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    response_format={"type": "text"},
                    messages=[
                        {"role": "user", "content": question},
                    ],
                )

                entry = OpenAIAnalysis()

                entry.id = sub["id"]
                entry.text = response.choices[0].message.content

                self.open_ai_analysis.create_opeai_analysis(entry)


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

    ap = AnalyticsProcessor()
    print("Processing submissions")
    submissions = ap.get_submissions()

    print("Running analytics")

    ap = OpenAIProccessor()
    # print("Processing submissions")
    ap.process(submissions)

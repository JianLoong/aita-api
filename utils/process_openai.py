import calendar
import logging
import os
from datetime import datetime, timedelta

from dotenv import find_dotenv, load_dotenv
from fastapi import HTTPException
from openai import AsyncOpenAI

from endpoints.database_config import DatabaseConfig
from endpoints.openai_inference_api import OpenAIInferenceAPI
from endpoints.submission_api import SubmissionAPI
from models.openai_analytics import OpenAIAnalysis


class OpenAIProccessor:
    def __init__(self, verbose: bool = False):
        load_dotenv(find_dotenv())
        self.api_key = os.environ.get("OPENAI_API_KEY")

        database_config = DatabaseConfig()
        engine = database_config.get_engine()

        self.submission_api = SubmissionAPI(engine)

        self.open_ai_analysis = OpenAIInferenceAPI(engine)

        self.client = AsyncOpenAI()

        self._verbose: bool = verbose

    async def process(self):
        self._verbose is True and print("Creating/Updating OPENAI Analysis")

        today = datetime.today()
        start = datetime(today.year, today.month, today.day) + timedelta(1)
        yesterday = start - timedelta(2)

        # Convert time to UTC time
        start_utc = calendar.timegm(start.timetuple())
        yesterday_utc = calendar.timegm(yesterday.timetuple())

        submissions = self.submission_api.search_submission(
            start_utc=yesterday_utc, end_utc=start_utc, limit=10000
        )

        self._verbose is True and print(
            f"Number of OpenAI Submissions {len(submissions)}"
        )

        for sub in submissions:
            try:
                self.open_ai_analysis.read_openai_inference(sub.id)
                self._verbose is True and print(
                    f"OpenAI analysis exist for {sub.title} skipping"
                )

            except HTTPException:
                # Doesnt exist so process
                print(f"Creating OpenAI Analysis for {sub.id} {sub.title}")
                text = self.submission_api.read_submission(sub.id)
                question = """
                Based on the following context, is the author an asshole? {selftext}
                """.format(
                    selftext=text
                )

                response = await self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    response_format={"type": "text"},
                    messages=[
                        {"role": "user", "content": question},
                    ],
                )

                entry = OpenAIAnalysis()

                entry.id = sub.id
                entry.text = response.choices[0].message.content

                self.open_ai_analysis.create_opeai_analysis(entry)

        self._verbose is True and print("OpenAI analysis completed.")

import logging
import os
from fastapi import HTTPException
from openai import OpenAI

from dotenv import dotenv_values
from endpoints.openai_inference_api import OpenAIInferenceAPI
from endpoints.submission_api import SubmissionAPI
from models.openai_analytics import OpenAIAnalysis


class OpenAIProccessor:
    def __init__(self):
        logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

        config = dotenv_values(".env")
        self.api_key = config.get("OPENAI_API_KEY")

        self.client = OpenAI()

        self.sep = SubmissionAPI()

    def process(self):
        id = 0

        for i in range(999, 2000):
            id = i

            open_ai_analysis = OpenAIInferenceAPI()

            try:
                open_ai_analysis.read_openai_inference(id)

                logging.info("Analysis exist. Skipping")
            except HTTPException:
                # Doesnt exist so process
                text = self.sep.read_submission(id)
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

                open_ai_analysis = OpenAIInferenceAPI()

                entry = OpenAIAnalysis()

                entry.id = id
                entry.text = response.choices[0].message.content

                open_ai_analysis.create_opeai_analysis(entry)


def main():
    oap = OpenAIProccessor()

    oap.process()


if __name__ == "__main__":
    main()

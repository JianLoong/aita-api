import sqlalchemy
from dotenv import find_dotenv, load_dotenv
from sqlmodel import Session

from endpoints.database_config import DatabaseConfig


class FTSProcessor:
    _instance = None
    _verbose = False

    def _configure_agent(self) -> None:
        load_dotenv(find_dotenv(), override=True)

        database_config = DatabaseConfig()
        self.engine = database_config.get_engine()

    def __new__(cls, verbose: bool = False):
        if cls._instance is None:
            cls._instance = super(FTSProcessor, cls).__new__(cls)
            cls._instance._configure_agent()
            cls._instance._verbose = verbose

        return cls._instance

    def process(self) -> None:
        try:
            with Session(self.engine) as session:
                statement = """
                    DROP TABLE IF EXISTS submission_fts;
                """

                sqlText = sqlalchemy.sql.text(statement)

                session.exec(sqlText)

                statement = """
                    CREATE VIRTUAL TABLE submission_fts USING fts5(id, title, selftext);
                """

                sqlText = sqlalchemy.sql.text(statement)

                session.exec(sqlText)

                statement = """
                    INSERT INTO submission_fts SELECT id, title, selftext FROM submission;
                """

                sqlText = sqlalchemy.sql.text(statement)

                session.exec(sqlText)

                session.commit()

                session.close()

        except Exception as e:
            print(e)


if __name__ == "__main__":
    fts_processor = FTSProcessor()

    fts_processor.process()

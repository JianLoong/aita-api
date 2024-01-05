from os import listdir
from os.path import isfile, join
import json

from sqlmodel import SQLModel, Session, create_engine
from models.breakdown import Breakdown

from models.summary import Summary


sqlite_file_name = "AmItheAsshole.db"
sqlite_url = f"sqlite:///database//{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=False)

mypath = r"C:\Users\Jian\Documents\GitHub\reddit-store\docs\api\summary"

onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]

session = Session(engine)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


create_db_and_tables()

for name in onlyfiles:
    with open(mypath + "\\" + name, "r+") as f:
        entry = json.load(f)
        # print(entry.get("word_freq"))

        id = entry.get("id")
        afinn = entry.get("afinn")
        emotion = entry.get("emotion")
        word_freq = entry.get("word_freq")
        counts = entry.get("counts")
        summary = Summary(
            id=id, afinn=afinn, word_freq=word_freq, emotion=emotion, counts=counts
        )

        nta_count = counts.get("nta_count")
        yta_count = counts.get("yta_count")
        esh_count = counts.get("esh_count")
        info_count = counts.get("info_count")
        nah_count = counts.get("nah_count")

        breakdown = Breakdown(
            id=id,
            nta=nta_count,
            yta=yta_count,
            esh=esh_count,
            info=info_count,
            nah=nah_count,
        )

        session.add(summary)
        session.add(breakdown)

session.commit()

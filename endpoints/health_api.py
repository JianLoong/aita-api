import time
from datetime import datetime

import psutil
import sqlalchemy
from fastapi import APIRouter
from sqlmodel import Session, select

from models.comment import Comment
from models.health import Health
from models.openai_analytics import OpenAIAnalysis
from models.submission import Submission
from models.summary import Summary


class HealthAPI:
    """

    Notes:
        https://thinhdanggroup.github.io/health-check-api/
        https://snyk.io/advisor/python/psutil/functions/psutil.disk_usage
    """

    def get_hdd(self):
        try:
            hdd = psutil.disk_partitions()
            data = []
            for each in hdd:
                device = each.device
                path = each.mountpoint
                fstype = each.fstype

                drive = psutil.disk_usage(path)
                total = drive.total
                total = total / 1000000000
                used = drive.used
                used = used / 1000000000
                free = drive.free
                free = free / 1000000000
                percent = drive.percent
                drives = {
                    "device": device,
                    "path": path,
                    "fstype": fstype,
                    "total": float("{0: .2f}".format(total)),
                    "used": float("{0: .2f}".format(used)),
                    "free": float("{0: .2f}".format(free)),
                    "percent": percent,
                }
                data.append(drives)
            if data:
                return data

        except Exception as e:
            print(e)

    def __init__(self, engine):
        self.engine = engine
        self.router = APIRouter()

        self.engine = engine
        self._setup_summary_routes()

    def _setup_summary_routes(self) -> None:
        self.router.add_api_route(
            "/health",
            self.read_health,
            methods=["GET"],
            tags=["Health"],
            description="Health Check for the AITA API",
        )

    def read_health(self) -> Health:
        with Session(self.engine) as session:
            submission_count = session.exec(
                select(sqlalchemy.func.count(Submission.id))
            ).one()

            comment_count = session.exec(
                select(sqlalchemy.func.count(Comment.id))
            ).one()

            openai_analysis_count = session.exec(
                select(sqlalchemy.func.count(OpenAIAnalysis.id))
            ).one()

            summary_count = session.exec(
                select(sqlalchemy.func.count(Summary.id))
            ).one()

        counts = {
            "submissionCount": submission_count,
            "commentCount": comment_count,
            "openAIAnalysisCount": openai_analysis_count,
            "summaryCount": summary_count,
        }

        health_check = Health(
            counts=counts, engine=str(self.engine), disk=self.get_hdd()
        )

        return health_check

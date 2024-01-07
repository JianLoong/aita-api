from datetime import datetime
from fastapi import APIRouter

import time
import sqlalchemy
import psutil

from sqlmodel import Session, select

from models.comment import Comment
from models.openai_analytics import OpenAIAnalysis
from models.submission import Submission


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
            "/health", self.read_health, methods=["GET"], tags=["Health"]
        )

    def read_health(self):
        health = dict()

        end_time = None

        with Session(self.engine) as session:
            start_time = time.time()
            submission_count = session.exec(
                select(sqlalchemy.func.count(Submission.id))
            ).one()

            comment_count = session.exec(
                select(sqlalchemy.func.count(Comment.id))
            ).one()

            openai_analysis_count = session.exec(
                select(sqlalchemy.func.count(OpenAIAnalysis.id))
            ).one()

            end_time = time.time() - start_time

        health["message"] = "It works"
        health["description"] = "AITA API Health Check"
        health["timestamp"] = datetime.now()
        health["uptime"] = time.monotonic()
        health["engine"] = str(self.engine)
        health["counts"] = {
            "submissionCount": submission_count,
            "commentCount": comment_count,
            "openAIAnalysisCount": openai_analysis_count,
        }
        health["dbResponseTime"] = end_time / 3
        health["cpuPercent"] = psutil.cpu_percent()
        health["virtualMemory"] = psutil.virtual_memory()
        health["memoryUsed"] = psutil.virtual_memory()[2]
        health["disk"] = self.get_hdd()

        return health

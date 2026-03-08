import os

from celery import Celery


BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1")

celery_app = Celery(
    "naukri_auto_apply",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["backend.workers.pipeline_tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    task_ignore_result=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)

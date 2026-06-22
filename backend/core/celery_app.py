from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "agrosmart",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.analytics",
        "app.tasks.alerts",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tashkent",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
    task_soft_time_limit=300,
    worker_max_tasks_per_child=1000,
)

celery_app.conf.beat_schedule = {
    "calculate-daily-farm-metrics": {
        "task": "app.tasks.analytics.calculate_daily_farm_metrics",
        "schedule": crontab(
            hour=settings.CELERY_DAILY_METRICS_HOUR,
            minute=settings.CELERY_DAILY_METRICS_MINUTE,
        ),
        "options": {"expires": 600},
    },
    "detect-all-alerts": {
        "task": "app.tasks.alerts.detect_all_alerts",
        "schedule": crontab(
            hour=settings.CELERY_ALERTS_HOUR,
            minute=settings.CELERY_ALERTS_MINUTE,
        ),
        "options": {"expires": 600},
    },
}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def debug_task(self) -> str:
    return f"Celery is working. Request: {self.request!r}"

from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ep_leads",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Jerusalem",
    enable_utc=True,
    task_acks_late=True,
    worker_max_tasks_per_child=200,
    task_default_retry_delay=60,
)

# Default schedule: daily full scan at 06:00 Israel time + closing-tender/alert
# sweeps every hour. Per-source frequency (spec section 19) is additionally
# respected inside run_scheduled_scans, which only actually scans sources whose
# own scan_frequency says they're due.
celery_app.conf.beat_schedule = {
    "scheduled-scan-sweep": {
        "task": "app.workers.tasks.run_scheduled_scans",
        "schedule": crontab(minute=0),  # every hour on the hour; each source enforces its own cadence
    },
    "check-closing-tenders": {
        "task": "app.workers.tasks.check_closing_tenders",
        "schedule": crontab(minute=15, hour="*/3"),
    },
    "check-stale-leads": {
        "task": "app.workers.tasks.check_changes_all",
        "schedule": crontab(minute=30, hour=4),
    },
}

"""Registers the recurring notification jobs, then keeps them firing: python scheduler.py

This process must keep running: rq-scheduler only moves a job onto the queue when its
run() loop sees it is due. Run worker.py alongside it to execute the jobs.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable

from rq_scheduler import Scheduler

from app.core.queue import notification_queue, rq_redis_conn
from app.jobs.notification_jobs import (
    scan_and_notify_expiring_batches,
    scan_and_notify_low_stock_and_pending_pos,
)

logger = logging.getLogger(__name__)

HOURLY_SECONDS = 3600
DAILY_SECONDS = 86400

# (job, repeat interval in seconds)
RECURRING_JOBS: tuple[tuple[Callable[[], None], int], ...] = (
    (scan_and_notify_expiring_batches, HOURLY_SECONDS),
    (scan_and_notify_low_stock_and_pending_pos, DAILY_SECONDS),
)


def register_jobs(scheduler: Scheduler) -> None:
    names = {f"{job.__module__}.{job.__name__}" for job, _ in RECURRING_JOBS}
    # Restarts would otherwise stack a second copy of every recurring job in Redis.
    for existing in scheduler.get_jobs():
        if existing.func_name in names:
            scheduler.cancel(existing)

    first_run = datetime.now(timezone.utc) + timedelta(seconds=15)
    for job, interval in RECURRING_JOBS:
        scheduler.schedule(scheduled_time=first_run, func=job, interval=interval, repeat=None)
        logger.info("Scheduled %s every %ss", job.__name__, interval)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Same queue the worker listens on; the library default ("default") would never be consumed.
    scheduler = Scheduler(queue_name=notification_queue.name, connection=rq_redis_conn)
    register_jobs(scheduler)
    scheduler.run()

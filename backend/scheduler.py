from datetime import datetime, timedelta

from rq_scheduler import Scheduler

from app.core.queue import rq_redis_conn
from app.jobs.notification_jobs import (
    scan_and_notify_low_stock_and_pending_pos,
    scan_and_notify_expiring_batches,
)

scheduler = Scheduler(connection=rq_redis_conn)

# Clear any previously scheduled instances of this job to avoid duplicates on restart
for job in scheduler.get_jobs():
    if job.func_name == "app.jobs.notification_jobs.scan_and_notify_low_stock_and_pending_pos":
        scheduler.cancel(job)
    elif job.func_name == "app.jobs.notification_jobs.scan_and_notify_expiring_batches":
        scheduler.cancel(job)

scheduler.schedule(
    scheduled_time=datetime.utcnow() + timedelta(seconds=15),
    func=scan_and_notify_expiring_batches,
    interval=3600,
    repeat=None,
)

print("Scheduled: expiring batches scan, every hour.")
from datetime import datetime, timedelta

from rq_scheduler import Scheduler

from app.core.queue import rq_redis_conn
from app.jobs.notification_jobs import scan_and_notify_low_stock_and_pending_pos

scheduler = Scheduler(connection=rq_redis_conn)

# Clear any previously scheduled instances of this job to avoid duplicates on restart
for job in scheduler.get_jobs():
    if job.func_name == "app.jobs.notification_jobs.scan_and_notify_low_stock_and_pending_pos":
        scheduler.cancel(job)

scheduler.schedule(
    scheduled_time=datetime.utcnow() + timedelta(seconds=10),  # first run soon, for easy testing
    func=scan_and_notify_low_stock_and_pending_pos,
    interval=3600,  # then every hour
    repeat=None,  # repeat forever
)

print("Scheduled: low-stock/pending-PO scan, every hour.")
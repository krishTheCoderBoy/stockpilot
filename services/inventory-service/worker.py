"""RQ worker for inventory-service background jobs: python worker.py"""
import logging

from rq import SimpleWorker

from app.core.queue import notification_queue, rq_redis_conn

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # SimpleWorker runs jobs in-process instead of forking, so it also works on Windows
    # development machines.
    SimpleWorker([notification_queue], connection=rq_redis_conn).work()

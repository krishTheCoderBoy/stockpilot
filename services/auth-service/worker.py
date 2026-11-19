"""RQ worker for auth-service's email queue (login codes, username recovery): python worker.py

The plain `rq worker` command ignores this service's settings and would look for Redis on
localhost; this entrypoint uses the same Redis connection as the app itself.
"""
import logging

from rq import SimpleWorker

from app.core.queue import email_queue, rq_redis_conn

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # SimpleWorker runs jobs in-process instead of forking, so it also works on Windows.
    SimpleWorker([email_queue], connection=rq_redis_conn).work()

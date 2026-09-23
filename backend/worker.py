from rq import SimpleWorker

from app.core.queue import email_queue, rq_redis_conn

if __name__ == "__main__":
    worker = SimpleWorker([email_queue], connection=rq_redis_conn)
    worker.work()
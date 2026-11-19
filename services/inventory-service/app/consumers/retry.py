"""Bounded-retry, delayed-redelivery, dead-letter and idempotency handling shared by consumers."""
import json
import logging
from typing import Callable

import pika
from pika.adapters.blocking_connection import BlockingChannel

from app.core.events.publisher import EXCHANGE_NAME
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY_MS = 5000
DEDUP_TTL_SECONDS = 86400  # 24h covers any realistic redelivery window
RETRY_HEADER = "x-retry-count"


def retry_queue_name(queue_name: str) -> str:
    return f"{queue_name}.retry"


def dead_letter_queue_name(queue_name: str) -> str:
    return f"{queue_name}.dlq"


def declare_consumer_topology(
    channel: BlockingChannel, queue_name: str, routing_keys: list[str]
) -> None:
    """Declare main, retry and dead-letter queues for one consumer.

    The main queue carries no x-arguments on purpose: queues declared by earlier
    versions had none, and redeclaring with different arguments fails with
    PRECONDITION_FAILED. Retries and dead-lettering are therefore explicit publishes
    to per-consumer queues via the default exchange, which also keeps one consumer's
    retries from fanning out into another consumer's queue.
    """
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="topic", durable=True)
    channel.queue_declare(queue=queue_name, durable=True)
    # Messages wait out the TTL here, then dead-letter straight back to the main queue.
    channel.queue_declare(
        queue=retry_queue_name(queue_name),
        durable=True,
        arguments={
            "x-message-ttl": RETRY_DELAY_MS,
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": queue_name,
        },
    )
    channel.queue_declare(queue=dead_letter_queue_name(queue_name), durable=True)
    for routing_key in routing_keys:
        channel.queue_bind(exchange=EXCHANGE_NAME, queue=queue_name, routing_key=routing_key)


def _dedup_key(queue_name: str, event_id: str) -> str:
    # Namespaced per consumer so two consumers of the same event never suppress each other.
    return f"processed_event:{queue_name}:{event_id}"


def _already_processed(key: str) -> bool:
    try:
        return bool(redis_client.get(key))
    except Exception:
        # A Redis outage must not halt consumption; the cost is a possible duplicate
        # if RabbitMQ redelivers during the outage.
        logger.exception("Dedup cache unavailable; processing without duplicate check")
        return False


def _mark_processed(key: str) -> None:
    try:
        redis_client.set(key, "1", ex=DEDUP_TTL_SECONDS)
    except Exception:
        logger.exception("Could not record dedup key %s", key)


def _republish(
    channel: BlockingChannel,
    target_queue: str,
    body: bytes,
    properties: pika.BasicProperties,
    headers: dict,
) -> None:
    channel.basic_publish(
        exchange="",
        routing_key=target_queue,
        body=body,
        properties=pika.BasicProperties(
            headers=headers,
            content_type=properties.content_type,
            delivery_mode=2,
        ),
    )


def handle_delivery(
    channel: BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.BasicProperties,
    body: bytes,
    queue_name: str,
    process: Callable[[dict], None],
) -> None:
    """Run `process` at most once per event_id, retrying failures a bounded number of times.

    The dedup key is written only after `process` returns, so a failed attempt is
    never mistaken for a completed one on redelivery.
    """
    headers = dict(properties.headers or {})
    try:
        event = json.loads(body)
        event_id = str(event["event_id"])
    except (ValueError, KeyError, TypeError):
        # Malformed payloads will never succeed, so retrying them only burns attempts.
        logger.exception("Unparseable message on %s; dead-lettering", queue_name)
        _dead_letter_or_requeue(channel, method, properties, body, queue_name, headers, "unparseable")
        return

    key = _dedup_key(queue_name, event_id)
    if _already_processed(key):
        channel.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        process(event)
    except Exception as exc:
        retry_count = int(headers.get(RETRY_HEADER, 0))
        logger.exception(
            "Consumer %s failed on event %s (attempt %s of %s)",
            queue_name, event_id, retry_count + 1, MAX_RETRIES + 1,
        )
        headers["x-last-error"] = repr(exc)[:500]
        if retry_count < MAX_RETRIES:
            headers[RETRY_HEADER] = retry_count + 1
            try:
                _republish(channel, retry_queue_name(queue_name), body, properties, headers)
                channel.basic_ack(delivery_tag=method.delivery_tag)
            except Exception:
                logger.exception("Could not schedule retry; requeueing on %s", queue_name)
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        else:
            _dead_letter_or_requeue(channel, method, properties, body, queue_name, headers, "max retries")
        return

    _mark_processed(key)
    channel.basic_ack(delivery_tag=method.delivery_tag)


def _dead_letter_or_requeue(
    channel: BlockingChannel,
    method: pika.spec.Basic.Deliver,
    properties: pika.BasicProperties,
    body: bytes,
    queue_name: str,
    headers: dict,
    reason: str,
) -> None:
    headers["x-dead-letter-reason"] = reason
    try:
        _republish(channel, dead_letter_queue_name(queue_name), body, properties, headers)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception:
        # Losing the message is worse than seeing it again, so fall back to a requeue.
        logger.exception("Could not dead-letter message; requeueing on %s", queue_name)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

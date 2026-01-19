"""Celery tasks for the ingestion pipeline."""
import os

from celery import Celery

_broker = os.environ.get(
    "CELERY_BROKER_URL",
    "amqp://{user}:{pw}@{host}:{port}//".format(
        user=os.environ.get("RABBITMQ_USER", "africgraph"),
        pw=os.environ.get("RABBITMQ_PASSWORD", ""),
        host=os.environ.get("RABBITMQ_HOST", "rabbitmq"),
        port=os.environ.get("RABBITMQ_PORT", "5672"),
    ),
)

app = Celery("ingestion", broker=_broker)
app.conf.task_serializer = "json"
app.conf.accept_content = ["json"]
app.conf.result_serializer = "json"
app.conf.timezone = "UTC"
app.conf.enable_utc = True

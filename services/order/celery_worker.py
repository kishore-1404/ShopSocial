from celery import Celery
import time
import os


DEFAULT_REDIS_URL = "redis://redis:6379/0"
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", DEFAULT_REDIS_URL)
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)

celery_app = Celery(
    'order_worker',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

@celery_app.task
def process_order(order_id):
    # Simulate background processing
    time.sleep(2)
    return f"Order {order_id} processed!"

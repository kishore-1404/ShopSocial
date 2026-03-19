from celery import Celery
import os

BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
app = Celery('order_worker', broker=BROKER_URL)

@app.task
def example_task(x, y):
    return x + y

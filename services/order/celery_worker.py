from celery import Celery
import time

celery_app = Celery(
    'order_worker',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)

@celery_app.task
def process_order(order_id):
    # Simulate background processing
    time.sleep(2)
    print(f"Order {order_id} processed!")
    return f"Order {order_id} processed!"

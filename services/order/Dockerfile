# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app


COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt
COPY . .
COPY seed.py /app/seed.py

EXPOSE 7000

CMD ["celery", "-A", "order_worker", "worker", "--loglevel=info"]

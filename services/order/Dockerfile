# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && \
    pip install celery psycopg2-binary redis sqlalchemy

EXPOSE 7000

CMD ["celery", "-A", "order_worker", "worker", "--loglevel=info"]

# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && \
    pip install flask graphene flask-graphql psycopg2-binary redis

EXPOSE 5000

CMD ["python", "app.py"]

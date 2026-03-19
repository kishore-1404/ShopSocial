# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && \
    pip install websockets redis psycopg2-binary sqlalchemy

EXPOSE 9000

CMD ["python", "chat_server.py"]

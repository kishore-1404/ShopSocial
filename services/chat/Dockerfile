# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

COPY chat/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt
COPY common /app/common
COPY chat /app

EXPOSE 9000

CMD ["python", "chat_server.py"]

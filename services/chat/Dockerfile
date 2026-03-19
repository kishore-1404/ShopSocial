# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt
COPY . .
COPY seed.py /app/seed.py

EXPOSE 9000

CMD ["python", "chat_server.py"]

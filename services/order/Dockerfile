# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app


COPY order/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt
COPY common /app/common
COPY order /app

EXPOSE 7000

CMD ["python", "app.py"]

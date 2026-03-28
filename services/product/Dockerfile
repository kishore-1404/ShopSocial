# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

COPY product/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt
COPY common /app/common
COPY product /app

EXPOSE 5000

CMD ["python", "app.py"]

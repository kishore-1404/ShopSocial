# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip && \
    pip install django djangorestframework psycopg2-binary redis

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

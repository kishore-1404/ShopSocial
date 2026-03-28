# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

COPY user/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt
COPY common /app/common
COPY user /app

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

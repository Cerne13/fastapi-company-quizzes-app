FROM tiangolo/uvicorn-gunicorn:python3.11-slim

LABEL maintainer='cerne313@gmail.com'
LABEL version='0.0.1'

WORKDIR /app

ENV PYTHONUNBUFFERED 1

COPY requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

ENV APP_PORT 8000
ENV APP_HOST 0.0.0.0

EXPOSE ${APP_PORT}

CMD uvicorn app.main:app --reload --host ${APP_HOST} --port ${APP_PORT}

FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install required libraries for psycopg2
RUN apt update -y && \
    apt upgrade -y && \
    apt install -y apt-utils && \
    apt install -y gettext && \
    apt install -y libpq-dev gcc && \
    pip install psycopg2

# Clean up apt cache to keep the image size small
RUN apt clean && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV HOME=/home/app
ENV APP_HOME=/home/app/web

WORKDIR $APP_HOME

COPY ./requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .


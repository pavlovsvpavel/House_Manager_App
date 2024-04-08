FROM python:3.11

RUN apt-get update
RUN apt upgrade -y
RUN apt-get install -y gettext

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV HOME=/home/app
ENV APP_HOME=/home/app/web

RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/static_files
RUN mkdir $APP_HOME/mediafiles


WORKDIR $APP_HOME

COPY ./requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .


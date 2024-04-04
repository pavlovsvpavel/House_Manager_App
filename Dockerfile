FROM python:3.11

RUN apt update -y && apt upgrade -y

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV HOME=/app
ENV STATICFILES_HOME=/app/static_files
ENV MEDIAFILES_HOME=/app/mediafiles

RUN mkdir -p $HOME
RUN mkdir -p $STATICFILES_HOME
RUN mkdir -p $MEDIAFILES_HOME

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY manage.py /app/manage.py
COPY nginx /app/nginx
COPY locale /app/locale_
COPY mediafiles /app/mediafiles
COPY templates /app/templates
COPY staticfiles /app/staticfiles
#COPY static_files /app/static_files
COPY house_manager /app/house_manager
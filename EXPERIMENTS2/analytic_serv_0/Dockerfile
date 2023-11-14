FROM python:3.8

# Достаточно изменить переменную для смены папок сборки и тд
ARG APP_NAME=helpdesk


WORKDIR /usr/src/$APP_NAME

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get -y update && \
    apt-get -y install libc-dev build-essential python3 python3-pip

RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/$APP_NAME/requirements.txt
RUN pip install -r requirements.txt

COPY . /usr/src/$APP_NAME/

RUN mkdir -p /usr/src/$APP_NAME
FROM python:3.11
LABEL authors="stanislavjpg"

ENTRYPOINT ["top", "-b"]

RUN mkdir /library

WORKDIR /library



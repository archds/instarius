FROM python:3.9-slim

WORKDIR /usr/src/app

# set up non-root user and required permissions
RUN adduser --disabled-password --quiet worker
RUN chmod -R 777 .

# install python requirements
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r ./requirements.txt

# copy application code
COPY app .

USER worker
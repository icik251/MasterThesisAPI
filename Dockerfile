FROM python:3.9.6-slim-buster
ENV PYTHONUNBUFFERED=1
COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
COPY . /app/
WORKDIR /app/
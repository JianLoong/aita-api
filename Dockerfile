# syntax=docker/dockerfile:1

# Comments are provided throughout this file to help you get started.
# If you need more help, visit the Dockerfile reference guide at
# https://docs.docker.com/engine/reference/builder/

ARG PYTHON_VERSION=3.10
FROM python:3.10-slim as base
RUN apt-get update && apt-get install build-essential -y

# Prevents Python from writing pyc files.
# ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Download dependencies as a separate step to take advantage of Docker's caching.
# Leverage a cache mount to /root/.cache/pip to speed up subsequent builds.
# Leverage a bind mount to requirements.txt to avoid having to copy them into
# into this layer.
# RUN python -m pip install --upgrade pip setuptools wheel

# RUN --mount=type=cache,target=/root/.cache/pip \
#     --mount=type=bind,source=requirements.txt,target=requirements.txt \
#     python -m pip install -r requirements.txt

# RUN python -m nltk.downloader punkt
# RUN python -m nltk.downloader stopwords
# Switch to the non-privileged user to run the application.
# USER appuser
RUN python -m pip install --upgrade pip
RUN python -m pip install --upgrade setuptools wheel

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

RUN python -m nltk.downloader punkt
RUN python -m nltk.downloader stopwords

# Copy the source code into the container.
COPY . .

# Expose the port that the application listens on.
EXPOSE 8000

# Run the application.
# CMD uvicorn main:app --port 8000 --host 0.0.0.0 --workers 4

CMD NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program uvicorn main:app --port 8000 --host 0.0.0.0 --workers 4 --ssl-keyfile ./key.pem --ssl-certfile ./cert.pem

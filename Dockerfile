FROM python:3.11-slim-buster as base
RUN apt-get update && pip install poetry==1.8.2
ARG HOME=/home/appuser
RUN groupadd -g 999 appuser && useradd -r -u 999 -g appuser appuser
WORKDIR ${HOME}
RUN chown -R appuser:appuser ${HOME}
USER appuser
COPY --chown=appuser:appuser  pyproject.toml poetry.lock ./

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True
# Don't try to write .pyc files on the import of source modules
ENV PYTHONDONTWRITEBYTECODE True
RUN poetry config virtualenvs.create true

# Note: The above can be a reusable parent image + security scanned, then imported below

FROM base as dev

RUN poetry install
# Copy local code to the container image.
ENV APP_HOME ./src
WORKDIR $APP_HOME

CMD exec poetry run uvicorn main:app --reload --host 0.0.0.0 --port $PORT

FROM base as prod

#RUN poetry sync
RUN poetry install --no-dev

# Copy local code to the container image.
ENV APP_HOME ./src
WORKDIR $APP_HOME
COPY src .

# uvicorn server
ENV WORKERS 4

# Run the web service on container startup. Here we use the gunicorn with uvicorn as worker process
CMD exec poetry run gunicorn main:app --workers $WORKERS -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 600
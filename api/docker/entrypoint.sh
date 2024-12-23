#!/bin/bash

set -e

if [[ "${MIGRATION_ENABLED}" == "true" ]]; then
  echo "Running migrations"
  flask db upgrade
fi

if [[ "${MODE}" == "worker" ]]; then
  celery -A app.celery worker -P ${CELERY_WORKER_CLASS:-gevent} -c ${CELERY_WORKER_AMOUNT:-1} --loglevel INFO \
    -Q ${CELERY_QUEUES:-dataset,generation,mail}
else
  if [[ "${DEBUG}" == "true" ]]; then
    echo "Running in debug mode"
    flask run --host=${DIFY_BIND_ADDRESS:-0.0.0.0} --port=${DIFY_PORT:-5001} --debug
  else
    echo "Running in production mode"
    gunicorn \
      --bind "${DIFY_BIND_ADDRESS:-0.0.0.0}:${DIFY_PORT:-5001}" \
      --workers ${SERVER_WORKER_AMOUNT:-1} \
      --worker-class ${SERVER_WORKER_CLASS:-gevent} \
      --timeout ${GUNICORN_TIMEOUT:-200} \
      --log-level debug \
      --log-file ./log/gunicorn.log \
      app:app
  fi
fi
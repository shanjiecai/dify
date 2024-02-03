# base image
FROM python:3.10-slim-bookworm AS base

LABEL maintainer="takatost@gmail.com"

# install packages
FROM base as packages

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc g++ libc-dev libffi-dev libgmp-dev libmpfr-dev libmpc-dev

COPY requirements.txt /requirements.txt

RUN pip install --prefix=/pkg -r requirements.txt

# production stage
FROM base AS production

ENV FLASK_APP app.py
ENV EDITION SELF_HOSTED
ENV DEPLOY_ENV PRODUCTION
ENV CONSOLE_API_URL http://127.0.0.1:5001
ENV CONSOLE_WEB_URL http://127.0.0.1:3000
ENV SERVICE_API_URL http://127.0.0.1:5001
ENV APP_WEB_URL http://127.0.0.1:3000

EXPOSE 5001

# set timezone
ENV TZ UTC

WORKDIR /app/api

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash curl wget vim nodejs ghostscript python3-tk ffmpeg libgmp-dev libmpfr-dev libmpc-dev \
    && apt-get autoremove \
    && rm -rf /var/lib/apt/lists/*

COPY --from=packages /pkg /usr/local
COPY . /app/api/

RUN python -c "from transformers import GPT2TokenizerFast; GPT2TokenizerFast.from_pretrained('gpt2')"
#RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1.tar.gz
ENV TRANSFORMERS_OFFLINE true

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ARG COMMIT_SHA
ENV COMMIT_SHA ${COMMIT_SHA}

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
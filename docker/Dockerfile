FROM python:3.9-alpine3.13

ARG UID=1000


ADD ../requirements.txt /tmp/requirements.txt
WORKDIR /app

RUN apk add --virtual .build-deps --no-cache --update \
    cmake make musl-dev gcc g++ gettext-dev libintl \
    git openssl-dev libffi-dev && \
    rm -rf musl-locales && \
    pip3 install -r /tmp/requirements.txt && \
    apk del .build-deps && \
    adduser \
    --disabled-password \
    --no-create-home \
    --shell /bin/bash \
    --gecos "" \
    --uid ${UID} \
    --home /app \
    app && \
    chown -R app:app /app

ADD . /app

ENV PORT=8080

USER app

CMD ["python", "main.py"]

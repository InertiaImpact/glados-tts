FROM python:3.10 as base
MAINTAINER Ben K <ben@sudo.is>

ENV TZ=UTC
ARG UID=1337
ARG NAME=glados
ENV TERM=xterm-256color

# COPY docker/apk/repositories /etc/apk/repositories

# RUN set -x && \
#     adduser --disabled-password --uid ${UID} glados && \
#     apk upgrade --update --no-cache && \
#     apk add --update --no-cache espeak-ng@testing curl


RUN set -x && \
    useradd -u ${UID} -m glados && \
    apt-get update && \
    apt-get install -y espeak-ng curl


ENV PATH "/home/glados/.local/bin:$PATH"
ENV PYTHONPATH "/usr/lib/python3.10/site-packages:/home/glados/.local/lib/python3.10/site-packages/"

FROM base as builder

RUN set -x && \
    ln -sfv /usr/local/src/glados /opt/glados
USER glados

RUN set -x && \
    python3 -m pip install poetry  && \
    python3 -m pip cache purge && \
    poetry self -V

COPY --chown=glados .flake8 poetry.lock pyproject.toml /usr/local/src/glados/
# change dir after COPY --chown, otherwise root owns it
WORKDIR /usr/local/src/glados/

# install dependencies with poetry and then freeze them in a file, so
# the final stage wont have to install them on each docker build
# unless they have changed
RUN set -x && \
    poetry install --without=dev --no-root --no-interaction --ansi && \
    poetry export --no-interaction --ansi --without-hashes --output requirements.txt && \
    poetry install --no-root --no-interaction --ansi && \
    poetry install --no-interaction --ansi


COPY --chown=glados README.md .
COPY --chown=glados glados_tts glados_tts
COPY --chown=glados tests tests

RUN set -x && \
    poetry run pytest --color=yes || true && \
    poetry run flake8 --color=always || true && \
    poetry install --with=dev --no-interaction --ansi

# building the python package here and copying the build files from it
# makes more sense than running the container with a bind mount,
# because this way we dont need to deal with permissions
RUN set -x && \
    poetry build --no-interaction

ARG PIP_REPO_URL="https://git.sudo.is/api/packages/ben/pypi"
ARG PIP_REPO_NAME="gitea"
RUN set -x && \
    python3 -m poetry config repositories.${PIP_REPO_NAME} ${PIP_REPO_URL} && \
    echo "repositories configured for poetry:" && \
    python3 -m poetry config repositories


ENTRYPOINT ["poetry"]
CMD ["build"]

FROM base as final
ARG NAME=glados
ENV NAME=glados
USER glados
COPY --chown=glados --from=builder /usr/local/src/glados/requirements.txt /usr/local/src/glados/
RUN set -x && \
    python3 -m pip install -r /usr/local/src/glados/requirements.txt && \
    python3 -m pip cache purge && \
    rm -v /usr/local/src/glados/requirements.txt
COPY --chown=glados --from=builder /usr/local/src/glados/dist /usr/local/src/glados/dist/

RUN set -x && \
    ls -1 /usr/local/src/glados/dist && \
    python3 -m pip install /usr/local/src/glados/dist/glados*tts-*.tar.gz && \
    rm -vrf /usr/local/src/glados/dist/

HEALTHCHECK --start-period=5s --interval=15s --timeout=1s \
    CMD curl -sSf http://localhost:8124/health

ENV LOGURU_BACKTRACE=0
ENV LOGURU_DIAGNOSE=0

ENTRYPOINT ["gladosctl"]
CMD ["restapi"]

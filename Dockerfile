FROM docker.io/python:3.10

# install FFmpeg
RUN apt-get -y update && apt-get -y upgrade && apt-get install -y --no-install-recommends ffmpeg

# Create dirs for:
# - Injecting config.yml: /root/.DANE
# - Mount point for input & output files: /mnt/dane-fs
# - Storing the source code: /src
RUN mkdir /root/.DANE /mnt/dane-fs /src /model

WORKDIR /src

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

COPY pyproject.toml poetry.lock ./

RUN pip install poetry==1.8.2

RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# copy the config file to /root/.DANE
COPY ./config/config.yml /root/.DANE

# copy the rest into the source dir
COPY ./ /src

# Write provenance info about software versions to file
RUN echo "dane-audio-extraction-worker;https://github.com/beeldengeluid/dane-audio-extraction-worker/commit/$(git rev-parse HEAD)" >> /software_provenance.txt

ENTRYPOINT ["./docker-entrypoint.sh"]

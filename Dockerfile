FROM docker.io/python:3.10

# Create dirs for:
# - Injecting config.yml: /root/.DANE
# - Mount point for input & output files: /mnt/dane-fs
# - Storing the source code: /src
RUN mkdir /root/.DANE /mnt/dane-fs /src /model


WORKDIR /src

# copy the pyproject file and install all the dependencies first
RUN pip install --upgrade pip
RUN pip install poetry
COPY ./pyproject.toml /src
RUN --mount=type=cache,target=/home/.cache/pypoetry/cache \
    --mount=type=cache,target=/home/.cache/pypoetry/artifacts \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi

# install FFmpeg
RUN apt-get -y update && apt-get -y upgrade && apt-get install -y --no-install-recommends ffmpeg

# copy the rest into the source dir
COPY ./ /src

FROM docker.io/python:3.11 AS req

RUN python3 -m pip install pipx && \
  python3 -m pipx ensurepath

RUN pipx install poetry==1.8.2 && \
  pipx inject poetry poetry-plugin-export && \
  pipx run poetry config warnings.export false

COPY ./poetry.lock ./poetry.lock
COPY ./pyproject.toml ./pyproject.toml
RUN pipx run poetry export --format requirements.txt --output requirements.txt

FROM docker.io/python:3.11

# install FFmpeg
RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Create dirs for:
# - Storing the source code: /src
# - Storing the input & output files: /data
RUN mkdir /src /data

WORKDIR /src

COPY --from=req ./requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# copy the rest into the source dir
COPY ./ /src

ENTRYPOINT ["./docker-entrypoint.sh"]

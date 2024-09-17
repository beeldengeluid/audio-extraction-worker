# audio-extraction-worker
Worker that extracts audio from video (for further processing in other workers).

There are 2 ways in which the worker can be run:



## 1. Docker run (recommended)

1. Check if Docker is installed
2. Make sure you have the `.env.override` file in your local repo folder
3. Open your preferred terminal and navigate to the local repository folder
3. To build the image, execute the following command:
```
docker build . -t audio-extraction-worker
```
4. To run the worker, execute the following command:
```
docker compose up
```

## 2. Local run

All commands should be run within WSL if on Windows or within your terminal if on Linux.

1. Follow the steps [here](https://github.com/beeldengeluid/dane-example-worker/wiki/Setting-up-a-new-worker) (under "Adding `pyproject.toml` and generating a `poetry.lock` based on it") to install Poetry and the dependencies required to run the worker
2. Make sure you have the `.env.override` file in your local repo folder
3. Install `ffmpeg`. You can run this command, for example:
```
apt-get -y update && apt-get -y upgrade && apt-get install -y --no-install-recommends ffmpeg
```
4. Execute the following command:
```
./run.sh
```

## Expected run

The expected run of this worker should download the input video file if it isn't downloaded already in `/data/input/`, run ffmpeg with the arguments specified in `.env.override`, and output an audio file in `data/output/`. You can also configure the transfer of the output to an S3 bucket.

If you want to test the input file download, we recommend deleting the `/data/input/` folder (NOT the `/data` folder).

## Environment variables

The variables unique to this worker affect the output and are the following:

1. `AE_SAMPLERATE_HZ`: The sampling rate of the resulting audio file. Default value is `0` which means the sampling rate of the input video file will be used

2. `AE_FILE_EXTENSION`: The file extension of the output audio file. Default is `wav`

3. `AE_CONVERT_TO_MONO`: Whether the audio output should be converted to mono format. Defaults to `n` (no/False)

They can all be modified through the `.env.override` file and the full list of variables can be found in `.env`.

## Example data
You can find an example video input file in `/data/input/` and the resutlting audio output file in `/data/output/`.

## Pipeline of the worker

The pipeline is as follows:

`./run.sh`/`docker compose up` -> `main.py`

`main.py` checks if the configuration is correct and, if so, runs the pipeline

`main.py` -> `run_pipeline.py`

`run_pipeline.py` makes sure each step of the pipeline is executed successfully:

- Downloading the input file if it's not present -> `download.py`
- Running the audio extraction of the input -> `transcode.py`
- Transferring the output to S3 if configured

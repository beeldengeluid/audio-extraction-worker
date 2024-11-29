import logging
import sys
from base_util import LOG_FORMAT
from config import input_uri, output_uri


# initialises the root logger
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,  # configure a stream handler only for now (single handler)
    format=LOG_FORMAT,
)
logger = logging.getLogger()


def run_api(port: int):
    from api import api
    import uvicorn

    logger.info("Running audio extractor as a service")
    uvicorn.run(api, port=port, host="0.0.0.0")


def run_job(input_uri: str, output_uri: str):
    import run_pipeline

    logger.info("Running audio extraction as a one time job")
    if not input_uri or not output_uri:
        logger.error("Please supply the --input and --output params")
        return False

    run_pipeline.run(input_uri, output_uri)


# Start the worker
if __name__ == "__main__":
    from argparse import ArgumentParser
    from base_util import LOG_FORMAT

    # first read the CLI arguments
    parser = ArgumentParser(description="audio-extraction-worker")
    parser.add_argument("--service", action="store", dest="service", default="n")
    parser.add_argument("--input", action="store", dest="input_uri", default=input_uri)
    parser.add_argument(
        "--output", action="store", dest="output_uri", default=output_uri
    )
    parser.add_argument("--log", action="store", dest="loglevel", default="INFO")
    parser.add_argument("--port", action="store", dest="port", default="5333")
    args = parser.parse_args()

    # initialises the root logger
    logging.basicConfig(
        stream=sys.stdout,  # configure a stream handler only for now (single handler)
        format=LOG_FORMAT,
    )

    # setting the loglevel
    log_level = args.loglevel.upper()
    logger.setLevel(log_level)
    logger.info(f"Logger initialized (log level: {log_level})")
    logger.info(f"Got the following CMD line arguments: {args}")

    run_as_service = args.service == "y"

    if run_as_service:
        try:
            port = int(args.port)
            run_api(port)
        except ValueError:
            logger.error("--port must be a valid integer, quitting")
    else:
        run_job(args.input_uri, args.output_uri)

import logging
import os
import subprocess
import json
from typing import Tuple, List
from urllib.parse import urlparse


LOG_FORMAT = "%(asctime)s|%(levelname)s|%(process)d|%(module)s|%(funcName)s|%(lineno)d|%(message)s"
PROVENANCE_JSON_FILE = "ae_provenance.json"
logger = logging.getLogger(__name__)


# the file name without extension is used as asset ID
def get_asset_info(input_file: str) -> Tuple[str, str]:
    file_name = os.path.basename(input_file)
    asset_id, extension = os.path.splitext(file_name)
    logger.info(f"working with this asset ID {asset_id}")
    return asset_id, extension


def extension_to_mime_type(extension: str) -> str:
    mime_dict = {
        ".mov": "video/quicktime",
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
    }

    return mime_dict.get(extension, "application/octet-stream")


# used by transcode.py
def run_shell_command(command: List[str]) -> bool:
    cmd = " ".join(command)
    logger.info("Executing command:")
    logger.info(cmd)
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,  # needed to support file glob
        )

        stdout, stderr = process.communicate()
        logger.info(stdout)
        logger.error(stderr)
        logger.info(f"Process is done: return code {process.returncode}")
        return process.returncode == 0
    except subprocess.CalledProcessError:
        logger.exception("CalledProcessError")
        return False
    except Exception:
        logger.exception("Exception")
        return False


def validate_http_uri(http_uri: str) -> bool:
    o = urlparse(http_uri, allow_fragments=False)
    if o.scheme != "http" and o.scheme != "https":
        logger.error(f"Invalid protocol in {http_uri}")
        return False
    if o.path == "":
        logger.error(f"No object_name specified in {http_uri}")
        return False
    return True


def is_transcodable(extension):
    return extension in [".mov", ".mp4"]


def remove_all_input_output(path: str) -> bool:
    try:
        if os.path.exists(path):
            for file in os.listdir(path):
                os.remove(os.path.join(path, file))
            os.rmdir(path)
            logger.info("All data has been deleted")
        else:
            logger.warning(f"{path} not found")
            return False
        return True
    except OSError:
        return False


def save_provenance(provenance: dict, output_dir: str) -> bool:
    logger.info(f"Saving provenance to: {output_dir}")
    try:
        # write ae_provenance.json
        with open(
            os.path.join(output_dir, PROVENANCE_JSON_FILE), "w+", encoding="utf-8"
        ) as f:
            logger.info(provenance)
            json.dump(provenance, f, ensure_ascii=False, indent=4)
    except EnvironmentError as e:  # OSError or IOError...
        logger.exception(os.strerror(e.errno))
        return False

    return True

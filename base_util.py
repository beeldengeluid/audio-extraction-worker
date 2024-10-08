import logging
import os
import subprocess
from typing import Tuple, List


LOG_FORMAT = "%(asctime)s|%(levelname)s|%(process)d|%(module)s|%(funcName)s|%(lineno)d|%(message)s"
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

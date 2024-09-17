import logging
import os
from typing import Optional

import base_util
from base_util import data_base_dir
from config import ae_file_extension, ae_convert_to_mono, ae_samplerate_hz

logger = logging.getLogger(__name__)


def ffmpeg_transcode(input_path, asset_id, extension) -> Optional[str]:
    logger.info(
        f"Running audio extraction for input_path: {input_path} asset_id: ({asset_id}) extension: ({extension})"
    )

    # if the input format is not supported, fail
    if not _is_transcodable(extension):
        logger.error(f"input with extension {extension} is not transcodable")
        return None

    transcoded_file_path = os.path.join(
        data_base_dir, "output", f"{asset_id}.{ae_file_extension}"
    )

    # do not transcode if the output already exists
    if os.path.exists(transcoded_file_path):
        logger.info(
            f"{transcoded_file_path} already exists, exiting"
        )
        return transcoded_file_path

    # go ahead and transcode the input file
    success = extract_audio(
        input_path,
        transcoded_file_path,
    )
    if not success:
        logger.error("Transcode failed")
        return None

    logger.info(
        f"Transcode of {extension} successful, returning: {transcoded_file_path}"
    )

    return transcoded_file_path


def extract_audio(input_path: str, output_path: str) -> bool:
    logger.debug(f"Extracting audio from file: {input_path}")
    ffmpeg_cmd = ["ffmpeg", "-i", input_path]

    if ae_convert_to_mono:
        ffmpeg_cmd = ffmpeg_cmd + ["-ac", "1"]
    if ae_samplerate_hz != 0:
        ffmpeg_cmd = ffmpeg_cmd + ["-ar", str(ae_samplerate_hz)]

    output_dir, _ = os.path.split(output_path)
    if not os.path.exists(output_dir):
        logger.info(f"{output_dir} does not exist, creating it now")
        os.makedirs(output_dir)

    return base_util.run_shell_command(ffmpeg_cmd + [output_path])


def _is_transcodable(extension):
    return extension in [".mov", ".mp4"]

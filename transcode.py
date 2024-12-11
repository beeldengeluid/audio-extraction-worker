import logging
import os
import time

from base_util import Provenance, run_shell_command, remove_all_input_output
from config import data_base_dir
from config import ae_file_extension

logger = logging.getLogger(__name__)


def ffmpeg_audio_extraction(input_path, asset_id, extension) -> Provenance:
    logger.info(
        f"Running audio extraction for input_path: {input_path} asset_id: ({asset_id}) extension: ({extension})"
    )

    start_time = time.time()

    # Get FFmpeg version used (to add to prov)
    ffmpeg_ver = run_shell_command(["ffmpeg", "--version"], True)
    if not ffmpeg_ver:
        raise Exception("Running ffmpeg to extract audio failed")

    provenance = Provenance(
        activity_name="Audio extraction",
        activity_description="Checks if audio can be extracted from the input, then extracts it if so",
        start_time_unix=start_time,
        software_version=ffmpeg_ver,
        input_data=input_path,
    )

    # if the input format is not supported, fail
    if not _is_transcodable(extension):
        raise Exception(
            f"Audio extraction failure: Input with extension {extension} is not transcodable"
        )

    output_path = os.path.join(
        data_base_dir, asset_id, f"{asset_id}.{ae_file_extension}"
    )

    # delete output if it exists
    if os.path.exists(output_path):
        logger.info(f"File {output_path} already exists, overwriting...")
        remove_all_input_output(output_path)

    # go ahead and transcode the input file
    success = extract_audio(
        input_path,
        output_path,
    )
    if not success:
        raise Exception("Running ffmpeg to extract audio failed")

    logger.info(
        f"Audio extraction of {input_path} successful, returning: {output_path}"
    )

    provenance.processing_time_ms = (time.time() - start_time) * 1000
    provenance.output_data = output_path
    provenance.steps.append("Audio extraction successful")
    return provenance


def extract_audio(input_path: str, output_path: str) -> bool:
    logger.debug(f"Running ffmpeg for file: {input_path}")
    return run_shell_command(["ffmpeg", "-i", input_path, output_path])


def _is_transcodable(extension):
    return extension in [".mov", ".mp4"]

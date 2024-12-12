import logging
import os
import time

from base_util import (
    Provenance,
    run_shell_command,
    remove_all_input_output,
    run_shell_command_with_output,
)
from config import ae_file_extension

logger = logging.getLogger(__name__)


def ffmpeg_audio_extraction(
    input_file: str,
    asset_id: str,
    extension: str,
    output_path: str,
) -> dict:
    logger.info(
        f"Running audio extraction for input_path: {input_file} asset_id: ({asset_id}) extension: ({extension})"
    )

    start_time = time.time()

    # Get output of "ffmpeg -version"
    ffmpeg_ver_cmd = run_shell_command_with_output(["ffmpeg", "-version"])
    if not ffmpeg_ver_cmd:
        raise Exception("Running ffmpeg to extract audio failed")

    # Add only the ffmpeg version number info to prov
    ffmpeg_ver = " ".join(ffmpeg_ver_cmd.split()[:3])

    provenance = Provenance(
        activity_name="Audio extraction",
        activity_description="Checks if audio can be extracted from the input, then extracts it if so",
        start_time_unix=start_time,
        software_version=ffmpeg_ver,
        input_data=input_file,
    )

    # if the input format is not supported, fail
    if not _is_transcodable(extension):
        raise Exception(
            f"Audio extraction failure: Input with extension {extension} is not transcodable"
        )

    output_file = os.path.join(output_path, f"{asset_id}.{ae_file_extension}")

    # delete output if it exists
    if os.path.exists(output_file):
        logger.info(f"File {output_file} already exists, overwriting...")
        remove_all_input_output(output_file)

    # go ahead and transcode the input file
    success = extract_audio(
        input_file,
        output_file,
    )
    if not success:
        raise Exception("Running ffmpeg to extract audio failed")

    logger.info(
        f"Audio extraction of {input_file} successful, returning: {output_file}"
    )

    provenance.processing_time_ms = (time.time() - start_time) * 1000
    provenance.output_data = output_file
    provenance.steps.append("Audio extraction successful")
    return {"prov": provenance, "output_fn": f"{asset_id}.{ae_file_extension}"}


def extract_audio(input_path: str, output_path: str) -> bool:
    logger.debug(f"Running ffmpeg for file: {input_path}")
    return run_shell_command(["ffmpeg", "-i", input_path, output_path])


def _is_transcodable(extension):
    return extension in [".mov", ".mp4"]

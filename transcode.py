from dataclasses import dataclass
import logging
import os
import time

import base_util
from config import data_base_dir
from config import ae_file_extension, ae_convert_to_mono, ae_samplerate_hz

logger = logging.getLogger(__name__)


@dataclass
class AudioExtractionOutput:
    provenance: dict
    error: str = ""


def ffmpeg_audio_extraction(input_path, asset_id, extension) -> AudioExtractionOutput:
    logger.info(
        f"Running audio extraction for input_path: {input_path} asset_id: ({asset_id}) extension: ({extension})"
    )

    start_time = time.time()
    provenance = {
        "activity_name": "Audio extraction",
        "activity_description": "Checks if input needs transcoding, then extracts the audio if so",
        "processing_time_ms": -1,
        "start_time_unix": start_time,
        "parameters": [],
        "software_version": "",
        "input_data": input_path,
        "output_data": "",
        "steps": [],
    }

    # if the input format is not supported, fail
    if not _is_transcodable(extension):
        logger.error(f"input with extension {extension} is not transcodable")
        return AudioExtractionOutput(
            dict(),
            f"Audio extraction failure: Input with extension {extension} is not transcodable",
        )

    output_path = os.path.join(
        data_base_dir, asset_id, f"{asset_id}.{ae_file_extension}"
    )

    # do not transcode if the output already exists
    if os.path.exists(output_path):
        logger.info(f"{output_path} already exists!")
        end_time = (time.time() - start_time) * 1000
        provenance["output_data"] = output_path
        provenance["steps"].append(
            "Audio file is already available, no new extraction needed"
        )
        return AudioExtractionOutput(provenance)

    # go ahead and transcode the input file
    success = extract_audio(
        input_path,
        output_path,
    )
    if not success:
        logger.error("Running ffmpeg to extract audio failed")
        return AudioExtractionOutput(dict(), "Running ffmpeg to extract audio failed")

    logger.info(
        f"Audio extraction of {input_path} successful, returning: {output_path}"
    )

    end_time = (time.time() - start_time) * 1000
    provenance["processing_time_ms"] = end_time
    provenance["output_data"] = output_path
    provenance["steps"].append("Audio extraction successful")
    return AudioExtractionOutput(provenance)


def extract_audio(input_path: str, output_path: str) -> bool:
    logger.debug(f"Extracting audio from file: {input_path}")
    ffmpeg_cmd = ["ffmpeg", "-i", input_path]

    if ae_convert_to_mono:
        ffmpeg_cmd = ffmpeg_cmd + ["-ac", "1"]
    if ae_samplerate_hz != 0:
        ffmpeg_cmd = ffmpeg_cmd + ["-ar", str(ae_samplerate_hz)]

    return base_util.run_shell_command(ffmpeg_cmd + [output_path])


def _is_transcodable(extension):
    return extension in [".mov", ".mp4"]

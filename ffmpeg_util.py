from models import (
    AudioExtractionInput,
    AudioExtractionOutput,
    OutputType,
)
import logging
import time
import subprocess
from dane.config import cfg
from dane.provenance import Provenance
from io_util import (
    get_base_output_dir,
    get_output_file_path,
)


def apply_ffmpeg(
    video_input: AudioExtractionInput,
) -> AudioExtractionOutput:
    logger = logging.getLogger(__name__)
    logger.info("Starting model application")
    start = time.time() * 1000  # convert to ms
    destination = get_output_file_path(video_input.source_id, OutputType.AUDIO)
    ffmpeg_cmd = ["ffmpeg", "-i", video_input.input_file_path]
    if cfg.AUDIO_EXTRACTION_SETTINGS.CONVERT_TO_MONO:
        ffmpeg_cmd = ffmpeg_cmd + ["-ac", "1"]
    if cfg.AUDIO_EXTRACTION_SETTINGS.OUTPUT_SAMPLERATE_HZ != 0:
        ffmpeg_cmd = ffmpeg_cmd + [
            "-ar",
            str(cfg.AUDIO_EXTRACTION_SETTINGS.OUTPUT_SAMPLERATE_HZ),
        ]
    subprocess.call(ffmpeg_cmd + [destination])
    logger.info("Executed command:")
    logger.info(ffmpeg_cmd + [destination])
    end = time.time() * 1000  # convert to ms

    model_application_provenance = Provenance(
        activity_name="video2audio",
        activity_description="converted a video file to audio format",
        input_data=video_input.input_file_path,
        start_time_unix=start,
        parameters=cfg.AUDIO_EXTRACTION_SETTINGS,
        software_version="0.1.0",
        output_data=destination,
        processing_time_ms=end - start,
    )

    if not model_application_provenance:
        return AudioExtractionOutput(500, "Failed to apply model")

    return AudioExtractionOutput(
        200,
        "Succesfully applied model",
        get_base_output_dir(video_input.source_id),
        model_application_provenance,
    )

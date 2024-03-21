import logging
import subprocess
from typing import Tuple, Optional
import time
from dane.config import cfg
from dane.s3_util import validate_s3_uri
from io_util import (
    get_base_output_dir,
    get_output_file_path,
    get_s3_output_file_uri,
    generate_output_dirs,
    get_source_id_from_tar,
    obtain_input_file,
    transfer_output,
    delete_local_output,
    delete_input_file,
    validate_data_dirs,
)
from models import (
    CallbackResponse,
    AudioExtractionInput,
    AudioExtractionOutput,
    OutputType,
)
from dane.provenance import (
    Provenance,
    obtain_software_versions,
    generate_initial_provenance,
    stop_timer_and_persist_provenance_chain,
)


logger = logging.getLogger(__name__)
DANE_WORKER_ID = "dane-audio-extraction-worker"


# triggered by running: python worker.py --run-test-file
def run(input_file_path: str) -> Tuple[CallbackResponse, Optional[Provenance]]:
    # there must be an input file
    if not input_file_path:
        logger.error("input file empty")
        return {"state": 403, "message": "Error, no input file"}, []

    # check if the file system is setup properly
    if not validate_data_dirs():
        logger.info("ERROR: data dirs not configured properly")
        return {"state": 500, "message": "Input & output dirs not ok"}, []

    # create the top-level provenance
    # TODO: add proper name and description
    top_level_provenance = generate_initial_provenance(
        name="dane-audio-extraction-worker",
        description=(
            "DANE worker that extracts audio files from video files (for further processing in other DANE workers)"
        ),
        input_data={"input_file_path": input_file_path},
        parameters=dict(cfg.AUDIO_EXTRACTION_SETTINGS),
        software_version=obtain_software_versions(DANE_WORKER_ID),
    )
    provenance_chain = []  # will contain the steps of the top-level provenance

    # S3 URI, local tar.gz or locally extracted tar.gz is allowed
    if validate_s3_uri(input_file_path):
        model_input = obtain_input_file(input_file_path)
    else:
        if input_file_path.find(".tar.gz") != -1:
            source_id = get_source_id_from_tar(input_file_path)
        else:
            source_id = input_file_path.split("/")[-2]

        model_input = AudioExtractionInput(
            200,
            f"Processing tar.gz archive: {input_file_path}",
            source_id,
            input_file_path,
            None,  # no download provenance when using local file
        )

    # add the download provenance
    if model_input.provenance:
        provenance_chain.append(model_input.provenance)

    # first generate the output dirs
    generate_output_dirs(model_input.source_id)

    # apply model to input & extract features
    proc_result = apply_ffmpeg(model_input)

    if proc_result.provenance:
        provenance_chain.append(proc_result.provenance)

    # as a last piece of output, generate the provenance.json before packaging&uploading
    full_provenance_chain = stop_timer_and_persist_provenance_chain(
        provenance=top_level_provenance,
        output_data={
            "output_path": get_base_output_dir(model_input.source_id),
            "output_uri": get_s3_output_file_uri(model_input.source_id),
        },
        provenance_chain=provenance_chain,
        provenance_file_path=get_output_file_path(
            model_input.source_id, OutputType.PROVENANCE
        ),
    )

    # if all is ok, apply the I/O steps on the outputted features
    validated_output: CallbackResponse = apply_desired_io_on_output(
        model_input,
        proc_result,
        cfg.INPUT.DELETE_ON_COMPLETION,
        cfg.OUTPUT.DELETE_ON_COMPLETION,
        cfg.OUTPUT.TRANSFER_ON_COMPLETION,
    )
    logger.info("Results after applying desired I/O")
    logger.info(validated_output)
    return validated_output, full_provenance_chain


def apply_ffmpeg(
    video_input: AudioExtractionInput,
) -> AudioExtractionOutput:
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


# assesses the output and makes sure input & output is handled properly
def apply_desired_io_on_output(
    model_input: AudioExtractionInput,
    proc_result: AudioExtractionOutput,
    delete_input_on_completion: bool,
    delete_output_on_completion: bool,
    transfer_output_on_completion: bool,
) -> CallbackResponse:
    # raise exception on failure
    if proc_result.state != 200:
        logger.error(f"Could not process the input properly: {proc_result.message}")
        # something went wrong inside the work processor, return that response
        return {"state": proc_result.state, "message": proc_result.message}

    # process returned successfully, generate the output
    source_id = model_input.source_id
    output_path = get_base_output_dir(source_id)

    # transfer the output to S3 (if configured so)
    transfer_success = True
    if transfer_output_on_completion:
        transfer_success = transfer_output(source_id)

    # failure of transfer, impedes the workflow, so return error
    if not transfer_success:
        return {
            "state": 500,
            "message": "Failed to transfer output to S3",
        }

    # clear the output files (if configured so)
    if delete_output_on_completion:
        delete_success = delete_local_output(source_id)
        if not delete_success:
            # NOTE: just a warning for now, but one to keep an eye out for
            logger.warning(f"Could not delete output files: {output_path}")

    # clean the input file (if configured so)
    if not delete_input_file(
        model_input.input_file_path,
        model_input.source_id,
        delete_input_on_completion,
    ):
        return {
            "state": 500,
            "message": "Applied model, but could not delete the input file",
        }

    return {
        "state": 200,
        "message": "Successfully applied model",
    }

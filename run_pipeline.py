import logging
import os
import time
from typing import Optional
from config import (
    data_base_dir,
    s3_endpoint_url,
    ae_samplerate_hz,
    ae_file_extension,
    ae_convert_to_mono,
)
from download import download_uri
from base_util import (
    get_asset_info,
    remove_all_input_output,
    save_provenance,
    PROVENANCE_JSON_FILE,
)
from s3_util import S3Store, parse_s3_uri
from transcode import ffmpeg_audio_extraction

logger = logging.getLogger(__name__)


def run(input_uri: str, output_uri: str) -> Optional[str]:
    logger.info(f"Processing {input_uri} (save to --> {output_uri})")
    start_time = time.time()
    prov_steps = []  # track provenance
    # 1. download input
    result = download_uri(input_uri)
    logger.info(result)
    if result.error != "":
        logger.error("Could not obtain input, quitting...")
        return result.error

    prov_steps.append(result.provenance)

    input_path = result.file_path
    asset_id, extension = get_asset_info(input_path)
    output_dir = os.path.join(data_base_dir, asset_id)

    # 2. do the actual audio extraction
    prov_or_error = ffmpeg_audio_extraction(input_path, asset_id, extension)
    if prov_or_error.error != "":
        logger.error(
            "The audio extraction failed to yield a valid file to continue with, quitting..."
        )
        remove_all_input_output(output_dir)
        return prov_or_error.error
    else:
        prov_steps.append(prov_or_error.provenance)

    end_time = (time.time() - start_time) * 1000
    final_prov = {
        "activity_name": "Whisper ASR Worker",
        "activity_description": "Worker that gets a video/audio file as input and outputs JSON transcripts in various formats",
        "processing_time_ms": end_time,
        "start_time_unix": start_time,
        "parameters": {
            "samplerate_hz": ae_samplerate_hz,
            "file_extension": ae_file_extension,
            "convert_to_mono": ae_convert_to_mono,
        },
        "software_version": "",
        "input_data": input_uri,
        "output_data": output_uri if output_uri else output_dir,
        "steps": prov_steps,
    }

    prov_success = save_provenance(final_prov, output_dir)
    if not prov_success:
        logger.error("Could not save the provenance")
        remove_all_input_output(output_dir)
        return "Provenance failure: Could not save the provenance"

    # 3. transfer output
    if output_uri:
        success = transfer_output(output_dir, output_uri, asset_id)
        if not success:
            logger.error("Could not upload output to S3")
            remove_all_input_output(output_dir)
            return "Upload failure: Could not upload output to S3"
    else:
        logger.info("No output_uri specified, so all is done")
    return None


# if (S3) output_uri is supplied transfers data to S3 location
def transfer_output(output_path: str, output_uri: str, asset_id: str) -> bool:
    logger.info(f"Transferring {output_path} to S3 (destination={output_uri})")
    if not s3_endpoint_url:
        logger.warning("Transfer to S3 configured without an S3_ENDPOINT_URL!")
        return False

    s3_bucket, s3_folder_in_bucket = parse_s3_uri(output_uri)

    s3 = S3Store(s3_endpoint_url)
    return s3.transfer_to_s3(
        s3_bucket,
        s3_folder_in_bucket,
        [
            os.path.join(output_path, f"{asset_id}.{ae_file_extension}"),
            os.path.join(output_path, PROVENANCE_JSON_FILE),
        ],
    )

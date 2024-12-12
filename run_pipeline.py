import logging
import time
import os
from urllib.parse import urlparse
from download import download_uri
from base_util import (
    get_asset_info,
    remove_all_input_output,
    save_provenance,
    transfer_output,
    Provenance,
)
from transcode import ffmpeg_audio_extraction
from config import data_base_dir, prov_filename, ae_file_extension

logger = logging.getLogger(__name__)


def run(input_uri: str, output_uri: str = "") -> dict:
    logger.info(f"Processing {input_uri} (save to --> {output_uri})")
    start_time = time.time()
    prov_steps = []  # track provenance

    try:
        # 1. get all needed info about input
        fn = os.path.basename(urlparse(input_uri).path)
        asset_id, extension = get_asset_info(fn)
        input_dir = os.path.join(data_base_dir, asset_id)

        # 2. download input
        dl_result = download_uri(input_uri, input_dir, fn, extension)
        logger.info(dl_result)

        prov_steps.append(dl_result.provenance)

        # 3. do the actual audio extraction
        extraction_result = ffmpeg_audio_extraction(
            dl_result.file_path, asset_id, extension, input_dir
        )
        prov_steps.append(extraction_result["prov"])

        end_time = (time.time() - start_time) * 1000
        final_prov = Provenance(
            activity_name="Audio Extraction Worker",
            activity_description="Worker that gets a video file as input and outputs an audio file with a given extension",
            processing_time_ms=end_time,
            start_time_unix=start_time,
            parameters={
                "file_extension": ae_file_extension,
            },
            input_data=input_uri,
            output_data=output_uri if output_uri else input_dir,
            steps=prov_steps,
        )

        # 4. save provenance to json file
        save_provenance(final_prov, input_dir)

        # 5. transfer all output
        if output_uri:
            success = transfer_output(input_dir, output_uri, asset_id)
            if not success:
                remove_all_input_output(input_dir)
                raise Exception("Upload failure: Could not upload output to S3")
            remove_all_input_output(input_dir)
        else:
            logger.info("No output_uri specified, so all is done")

        return {"audio": extraction_result["output_fn"], "provenance": prov_filename}

    except Exception as e:
        logger.error(f"Worker failed! Exception raised: {e}")
        # Check if variable exists (might not if exception raised from download_uri)
        if "dl_result" in locals():
            remove_all_input_output(input_dir)
        raise e

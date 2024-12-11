import logging
import time
from config import (
    ae_file_extension,
)
from download import download_uri
from base_util import (
    get_asset_info,
    remove_all_input_output,
    save_provenance,
    transfer_output,
    Provenance,
)
from transcode import ffmpeg_audio_extraction

logger = logging.getLogger(__name__)


def run(input_uri: str, output_uri: str = "") -> bool:
    logger.info(f"Processing {input_uri} (save to --> {output_uri})")
    start_time = time.time()
    prov_steps = []  # track provenance

    try:
        # 1. download input
        dl_result = download_uri(input_uri)
        logger.info(dl_result)

        prov_steps.append(dl_result.provenance)

        input_path = dl_result.file_path
        asset_id, extension = get_asset_info(input_path)

        # 2. do the actual audio extraction
        extraction_prov = ffmpeg_audio_extraction(input_path, asset_id, extension)
        prov_steps.append(extraction_prov)

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
            output_data=output_uri if output_uri else dl_result.output_path,
            steps=prov_steps,
        )

        # 3. save provenance to json file
        save_provenance(final_prov, dl_result.output_path)

        # 4. transfer all output
        if output_uri:
            success = transfer_output(dl_result.output_path, output_uri, asset_id)
            if not success:
                remove_all_input_output(dl_result.output_path)
                raise Exception("Upload failure: Could not upload output to S3")
            remove_all_input_output(dl_result.output_path)
        else:
            logger.info("No output_uri specified, so all is done")

        return True

    except Exception as e:
        logger.error(f"Worker failed! Exception raised: {e}")
        remove_all_input_output(dl_result.output_path)
        raise e

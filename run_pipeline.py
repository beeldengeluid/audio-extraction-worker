import logging
import os
from config import s3_endpoint_url, s3_bucket, s3_folder_in_bucket
from download import download_uri
from base_util import get_asset_info, asr_output_dir
from s3_util import S3Store
from transcode import ffmpeg_transcode

logger = logging.getLogger(__name__)


def run(input_uri: str, output_uri: str) -> bool:
    logger.info(f"Processing {input_uri} (save to --> {output_uri})")
    # 1. download input
    result = download_uri(input_uri)
    logger.info(result)
    if not result:
        logger.error("Could not obtain input, quitting...")
        return False

    input_path = result.file_path
    asset_id, extension = get_asset_info(input_path)
    output_path = asr_output_dir(input_path)

    # 2. do the actual transcoding
    output_path = ffmpeg_transcode(input_path, asset_id, extension)
    if not output_path:
        logger.error("The transcode failed to yield a valid file to continue with")
        return False

    # 3. transfer output
    if output_uri:
        transfer_asr_output(output_path, asset_id)
    else:
        logger.info("No output_uri specified, so all is done")
    return True


# if (S3) output_uri is supplied transfers data to S3 location
def transfer_asr_output(output_path: str, asset_id: str) -> bool:
    logger.info(f"Transferring {output_path} to S3 (asset={asset_id})")
    if any(
        [
            not x
            for x in [
                s3_endpoint_url,
                s3_bucket,
                s3_folder_in_bucket,
            ]
        ]
    ):
        logger.warning(
            "TRANSFER_ON_COMPLETION configured without all the necessary S3 settings"
        )
        return False

    s3 = S3Store(s3_endpoint_url)
    return s3.transfer_to_s3(
        s3_bucket,
        os.path.join(
            s3_folder_in_bucket, asset_id
        ),  # assets/<program ID>__<carrier ID>
        output_path,
    )

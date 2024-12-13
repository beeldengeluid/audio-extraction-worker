import os
import validators


# mounting dir
data_base_dir = os.environ.get("DATA_BASE_DIR", "")

# s3 connection params
s3_endpoint_url = os.environ.get("S3_ENDPOINT_URL")
s3_bucket = os.environ.get("S3_BUCKET")
s3_folder_in_bucket = os.environ.get("S3_FOLDER_IN_BUCKET")

# Audio extraction params
ae_file_extension = os.environ.get("AE_FILE_EXTENSION", "wav")
prov_filename = os.environ.get("PROVENANCE_FILENAME", "ae_provenance.json")

assert data_base_dir, "Please add DATA_BASE_DIR to your environment"
assert data_base_dir not in [".", "/"], "Please enter an absolute, non-root path"
assert os.path.exists(data_base_dir), "DATA_BASE_DIR does not exist"

if s3_bucket or s3_endpoint_url or s3_folder_in_bucket:
    assert s3_bucket, "Please enter the S3_BUCKET to use"
    assert validators.url(s3_endpoint_url), "Please enter a valid S3_ENDPOINT_URL"
    assert s3_folder_in_bucket, "Please enter a path within the supplied S3 bucket"

assert ae_file_extension in [
    "wav",
    "mp3",
], "Please use one of: [wav, mp3] for AE_FILE_EXTENSION"

assert prov_filename, "Please add PROVENANCE_FILENAME to your environment"

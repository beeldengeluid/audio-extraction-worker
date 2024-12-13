import os
import validators


# mounting dir
DATA_BASE_DIR = os.environ.get("DATA_BASE_DIR", "")

# s3 connection params
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL")
S3_BUCKET = os.environ.get("S3_BUCKET")
S3_FOLDER_IN_BUCKET = os.environ.get("S3_FOLDER_IN_BUCKET")

# Audio extraction params
AE_FILE_EXTENSION = os.environ.get("AE_FILE_EXTENSION", "wav")
PROV_FILENAME = os.environ.get("PROVENANCE_FILENAME", "ae_provenance.json")

assert DATA_BASE_DIR, "Please add DATA_BASE_DIR to your environment"
assert DATA_BASE_DIR not in [".", "/"], "Please enter an absolute, non-root path"
assert os.path.exists(DATA_BASE_DIR), "DATA_BASE_DIR does not exist"

if S3_BUCKET or S3_ENDPOINT_URL or S3_FOLDER_IN_BUCKET:
    assert S3_BUCKET, "Please enter the S3_BUCKET to use"
    assert validators.url(S3_ENDPOINT_URL), "Please enter a valid S3_ENDPOINT_URL"
    assert S3_FOLDER_IN_BUCKET, "Please enter a path within the supplied S3 bucket"

assert AE_FILE_EXTENSION in [
    "wav",
    "mp3",
], "Please use one of: [wav, mp3] for AE_FILE_EXTENSION"

assert PROV_FILENAME, "Please add PROVENANCE_FILENAME to your environment"

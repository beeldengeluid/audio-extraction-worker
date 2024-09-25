import os
import validators


def assert_bool(param: str) -> bool:
    value = os.environ.get(param, "y")
    assert value in ["y", "n"], f"Please use y or n for {param}, not |{value}|"
    return value == "y"


def assert_int(param: str) -> int:
    value = os.environ.get(param, -1)
    try:
        return int(value)
    except ValueError:
        assert False, f"Please enter a valid number for {param}, not |{value}|"


# main input & output params
input_uri = os.environ.get("INPUT_URI", "")
output_uri = os.environ.get("OUTPUT_URI", "")

# mounting dir
data_base_dir = os.environ.get("DATA_BASE_DIR", "")

# s3 connection params
s3_endpoint_url = os.environ.get("S3_ENDPOINT_URL", "")
s3_bucket = os.environ.get("S3_BUCKET", "")
s3_folder_in_bucket = os.environ.get("S3_FOLDER_IN_BUCKET", "")

# Audio extraction params
ae_samplerate_hz = assert_int("AE_SAMPLERATE_HZ")
ae_file_extension = os.environ.get("AE_FILE_EXTENSION", "wav")
ae_convert_to_mono = assert_bool("AE_CONVERT_TO_MONO")

# validation for each param
if input_uri:
    if input_uri[0:5] != "s3://":
        assert validators.url(input_uri), "Please provide a valid INPUT_URI"

if output_uri:
    if output_uri[0:5] != "s3://":
        assert validators.url(output_uri), "Please provide a valid OUTPUT_URI"


assert data_base_dir, "Please add DATA_BASE_DIR to your environment"
assert data_base_dir not in [".", "/"], "Please enter an absolute, non-root path"
assert os.path.exists(data_base_dir), "DATA_BASE_DIR does not exist"

if s3_bucket or s3_endpoint_url or s3_folder_in_bucket:
    assert s3_bucket, "Please enter the S3_BUCKET to use"
    assert validators.url(s3_endpoint_url), "Please enter a valid S3_ENDPOINT_URL"
    assert s3_folder_in_bucket, "Please enter a path within the supplied S3 bucket"

assert ae_samplerate_hz >= 0, "The AE_SAMPLERATE_HZ must be positive"
assert ae_file_extension in [
    "wav",
    "mp3",
], "Please use one of: [wav, mp3] for AE_FILE_EXTENSION"

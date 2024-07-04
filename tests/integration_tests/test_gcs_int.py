import json

from configuration.env import settings
from conftest import DESTINATION_BLOB_NAME


def test_read_from_emulator(gcs_utils, upload_test_file):
    # read the test file sent to test bucket
    input_file_from_emulator = gcs_utils.read_file(
        bucket_name=settings.target_bucket,
        source_blob_name=DESTINATION_BLOB_NAME,
    )
    gcs_utils.wipe_bucket(settings.target_bucket)
    assert json.loads(input_file_from_emulator) == [
 {
   "Name": "John Doe",
   "Age": 30,
   "Country": "United States"
 },
 {
   "Name": "Jane Doe",
   "Age": 25,
   "Country": "Canada"
 },
 {
   "Name": "Peter Smith",
   "Age": 40,
   "Country": "United Kingdom"
 }
]
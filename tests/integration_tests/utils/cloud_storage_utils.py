import io
import logging

from google.cloud import storage


class CloudStorageUtils:
    """Class for interacting with a Cloud Storage emulator"""

    def __init__(self):
        self.client = storage.Client()

    def wipe_bucket(self, bucket_name: str):
        bucket = self.client.get_bucket(bucket_name)
        blobs = bucket.list_blobs()
        for blob in blobs:
            blob.delete()
        print(f"All files deleted from bucket: {bucket_name}")

    def upload_file(self, bucket: str, file_name: str, file_path: str) -> None:
        """Uploads a file from a local file path"""
        bucket = self.client.bucket(bucket)
        blob = bucket.blob(file_name)
        blob.upload_from_filename(file_path)

    def upload_file_from_buffer(self, bucket: str, file_name: str, string_data) -> None:
        """Uploads a file from a string buffer"""
        bucket = self.client.bucket(bucket)
        logging.info(f"BUCKET {bucket}")
        blob = bucket.blob(file_name)
        logging.info(f"BLOB {blob}")
        string_io = io.StringIO(string_data)
        logging.info(f"STRINGIO {string_io}")
        bytes_io = io.BytesIO(string_io.getvalue().encode())
        logging.info(f"BYTESIO {bytes_io}")
        blob.upload_from_file(bytes_io, size=len(bytes_io.getvalue()))

    def read_file(self, bucket_name: str, source_blob_name: str):
        """Reads a file from GCS"""
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        file_as_bytes = blob.download_as_bytes()

        return file_as_bytes

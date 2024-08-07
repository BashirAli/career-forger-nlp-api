import io
import logging
import os
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

    def upload_entire_folder(self, bucket_name: str, folder_path: str, prefix: str = '') -> None:

        bucket = self.client.bucket(bucket_name)
        file_count = 0

        # Walk through the directory
        for root, _, files in os.walk(folder_path):
            for file in files:
                local_file_path = os.path.join(root, file)
                # Create a blob name with the prefix and relative path
                blob_name = os.path.join(prefix, os.path.relpath(local_file_path, folder_path))
                blob = bucket.blob(blob_name)
                blob.upload_from_filename(local_file_path)
                file_count += 1

            logging.info(
                f"Uploaded {file_count} files from folder '{folder_path}' to bucket '{bucket_name}' with prefix '{prefix}'")

    def download_entire_folder(self, bucket_name: str, folder_prefix: str, destination_folder: str) -> None:
        """Downloads all files from a specified folder in a bucket to a local directory"""
        bucket = self.client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=folder_prefix)

        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)

        for blob in blobs:
            # Remove the folder prefix from the blob name to get the relative path
            relative_path = os.path.relpath(blob.name, folder_prefix)
            local_path = os.path.join(destination_folder, relative_path)
            local_dir = os.path.dirname(local_path)

            if not os.path.exists(local_dir):
                os.makedirs(local_dir)

            # Only download files, skip directory blobs
            if not blob.name.endswith('/'):
                blob.download_to_filename(local_path)
                print(f"Downloaded {blob.name} to {local_path}")

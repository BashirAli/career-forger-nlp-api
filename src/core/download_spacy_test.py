import os
import tempfile
import spacy
from google.cloud import storage


class CloudStorageUtils:
    """Class for interacting with Google Cloud Storage"""

    def __init__(self):
        self.client = storage.Client()

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


# Initialize the CloudStorageUtils class
storage_utils = CloudStorageUtils()

# Define bucket name and model directory
bucket_name = 'test-bash-bucket'
model_folder_prefix = 'models/en_core_web_lg/'  # Make sure this points to the correct model directory

# Create a temporary directory to download the model
with tempfile.TemporaryDirectory() as temp_dir:
    # Download the entire model folder from GCS to the temporary directory
    storage_utils.download_entire_folder(bucket_name, model_folder_prefix, temp_dir)

    # Check if meta.json is present
    meta_path = os.path.join(temp_dir, 'meta.json')
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"meta.json not found in the model directory: {temp_dir}")

    # Load the spaCy model from the temporary directory
    nlp = spacy.load(temp_dir)

    # Test the loaded model with some text
    text = "SpaCy is an amazing NLP library."
    doc = nlp(text)

    # Print the named entities in the text
    for ent in doc.ents:
        print(ent.text, ent.label_)

    # Additional cleanup or checks if necessary
    print("Model loaded and tested successfully.")

# After the 'with' block, the temporary directory and its contents are automatically deleted

import base64
import json
from datetime import datetime


attributes = {
    "bucketId": "dummy_bucket",
    "eventTime": "2024-05-31T10:10:10.123431Z",
    "eventType": "OBJECT_FINALIZE",
    "notificationConfig": "config",
    "objectGeneration": "1234",
    "objectId": f"test/processed/2024/05/31/test_file.json",
    "payloadFormat": "JSON_API_V1",
}


valid_gcs_event_data = {
    "message": {
        "data": {
            "kind": "storage_object",
            "id": "dummy_bucket/test_file.json",
            "selfLink": "dummy_self_link",
            "name": f"test/2024/05/31/test_file.json",
            "bucket": "dummy_bucket",
            "generation": "1234",
            "metageneration": "1",
            "contentType": "text/plain",
            "timeCreated": str(datetime.now()),
            "updated": str(datetime.now()),
            "storageClass": "STANDARD",
            "timeStorageClassUpdated": str(datetime.now()),
            "size": "20",
            "md5Hash": "hash",
            "mediaLink": "dummy_link",
            "crc32c": "dummy",
            "etag": "dummy_etag",
        },
        "message_id": "test_message_id",
        "publish_time": "2024-05-31T10:10:10.012022+01:00",
        "attributes": attributes,
    }
}

invalid_test_missing_name = {
    "message": {
        "data": {
            "kind": "storage_object",
            "id": "dummy_bucket/test_file.json",
            "selfLink": "dummy_self_link",
            "bucket": "dummy_bucket",
            "generation": "1234",
            "metageneration": "1",
            "contentType": "text/csv",
            "timeCreated": str(datetime.now()),
            "updated": str(datetime.now()),
            "storageClass": "STANDARD",
            "timeStorageClassUpdated": str(datetime.now()),
            "size": "20",
            "md5Hash": "hash",
            "mediaLink": "dummy_link",
            "crc32c": "dummy",
            "etag": "dummy_etag",
        },
        "message_id": "test_message_id",
        "publish_time": "2024-05-31T10:10:10.012022+01:00",
        "attributes": attributes,
    }
}

invalid_test_missing_name_bytes = {
    "message": {
        "data": "ewogICAgICAgICAgICAiYnVja2V0IjogInRlc3Rfdm1faGFzYW4iCiAgICAgICAgfQ==",
        "message_id": "test_message_id",
        "publish_time": "2024-05-31T10:10:10.012022+01:00",
        "attributes": attributes,
    }
}

invalid_test_non_dict_data = {
    "message": {
        "data": [{"a": "b"}],
        "message_id": "test_message_id",
        "publish_time": "2024-05-31T10:10:10.012022+01:00",
        "attributes": attributes,
    }
}

invalid_test_missing_message_id = {
    "message": {
        "data": {
            "name": "test/2024/05/31/test_file.json",
            "bucket": "dummy_bucket",
        },
        "publish_time": "2024-05-31T10:10:10.012022+01:00",
        "attributes": attributes,
    }
}

from datetime import datetime

attributes = {
    "bucketId": "dummy_bucket"
}

valid_pubsub_eml_event_data = {
    "message": {
        "data": {
            "date_sent": "Thu, 1 Apr 2021 12:00:00 +0000",
            "sender": "sender@example.com",
            "recipient": "recipient@example.com",
            "title": "Test Email",
            "content_type": "text/plain",
            "content": "Your technical skills are impressive, especially your proficiency in Python and algorithms. However, "
                       "there is room for improvement in your knowledge of machine learning algorithms and data structures. "
                       "In non-technical aspects, your communication skills are excellent, and you work well in teams. "
                       "However, sometimes you struggle with time management and meeting deadlines, which can affect project "
                       "timelines. You might want to focus on developing your project management skills and improving your "
                       "ability to prioritise tasks effectively. Your involvement in extracurricular activities, such as the "
                       "coding club and volunteering for community projects, is commendable. You showed remarkable leadership "
                       "during the last project, but there were instances where you could have delegated tasks more "
                       "efficiently. For career advice, I suggest you keep honing your public speaking skills and seek "
                       "opportunities for mentorship to further enhance your leadership abilities."
        },
        "message_id": "test_message_id",
        "publish_time": str(datetime.now()),
        "attributes": attributes,
    }
}

valid_response_raw_dict = {
            "date_sent": "Thu, 1 Apr 2021 12:00:00 +0000",
            "sender": "sender@example.com",
            "recipient": "recipient@example.com",
            "title": "Test Email",
            "content_type": "text/plain",
            "content": "Your technical skills are impressive, especially your proficiency in Python and algorithms. However, "
                       "there is room for improvement in your knowledge of machine learning algorithms and data structures. "
                       "In non-technical aspects, your communication skills are excellent, and you work well in teams. "
                       "However, sometimes you struggle with time management and meeting deadlines, which can affect project "
                       "timelines. You might want to focus on developing your project management skills and improving your "
                       "ability to prioritise tasks effectively. Your involvement in extracurricular activities, such as the "
                       "coding club and volunteering for community projects, is commendable. You showed remarkable leadership "
                       "during the last project, but there were instances where you could have delegated tasks more "
                       "efficiently. For career advice, I suggest you keep honing your public speaking skills and seek "
                       "opportunities for mentorship to further enhance your leadership abilities."
        }


invalid_test_missing_fields = {
    "message": {
        "data": {

        },
        "message_id": "test_message_id",
        "publish_time": str(datetime.now()),
        "attributes": attributes,
    }
}

invalid_test_missing_fields_bytes = {
    "message": {
        "data": "ewogICAgICAgICAgICAiYnVja2V0IjogInRlc3Rfdm1faGFzYW4iCiAgICAgICAgfQ==",
        "message_id": "test_message_id",
        "publish_time": str(datetime.now()),
        "attributes": attributes,
    }
}

invalid_test_non_dict_data = {
    "message": {
        "data": [{"a": "b"}],
        "message_id": "test_message_id",
        "publish_time": str(datetime.now()),
        "attributes": attributes,
    }
}

invalid_test_missing_message_id = {
    "message": {
        "data": {
            "date_sent": "Thu, 1 Apr 2021 12:00:00 +0000",
            "sender": "sender@example.com",
            "recipient": "recipient@example.com",
            "title": "Test",
            "content_type": "text/plain",
            "content": "test"
        },
        "publish_time": str(datetime.now()),
        "attributes": attributes,
    }
}

import datetime
import decimal

import pytest

from gcp.pubsub import PubSubPublisher


def test_json_serial_datetime():
    message = datetime.datetime(2023, 5, 22, 12, 00, 00)
    result = PubSubPublisher.json_serial(message)
    assert result == "2023-05-22T12:00:00"


def test_json_serial_date():
    message = datetime.date(2023, 5, 22)
    result = PubSubPublisher.json_serial(message)
    assert result == "2023-05-22"


def test_json_serial_decimal():
    message = decimal.Decimal(1234.0)
    result = PubSubPublisher.json_serial(message)
    assert result == int(1234)


def test_json_serial_invalid_type():
    message = "test string"
    with pytest.raises(TypeError) as ex:
        result = PubSubPublisher.json_serial(message)
    assert str(ex.value) == "Type <class 'str'> is not serializable"

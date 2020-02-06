import struct
from io import BytesIO
from unittest.mock import patch

import pytest

from avrokafka import avrolib
from avrokafka.exceptions import SerializerError
from avrokafka.schema_registry import SchemaRegistry
from avrokafka.schema_registry.errors import IncompatibleSchemaVersion
from avrokafka.serde import AvroKeyValueSerde

TOPIC = "avrokafka-test-employee"
SCHEMA_REGISTRY_CLS = "avrokafka.schema_registry.SchemaRegistry"


def _schema_registry_mock(cls_mock, schema_id=None, schema_str=None):
    sr = cls_mock.return_value
    sr.schema_id_size = 4
    sr.get_schema.return_value = schema_str
    sr.register_schema.return_value = schema_id
    return sr


def test_value_deserialize_missing_magicbyte(employee_schema, employee_avro_data):
    with patch(SCHEMA_REGISTRY_CLS) as mock:
        sr = _schema_registry_mock(mock)
        avroSerde = AvroKeyValueSerde(sr, TOPIC)
        with pytest.raises(SerializerError) as e:
            avroSerde.value.deserialize(employee_avro_data)


def test_value_deserialize_none(employee_schema, employee_avro_data):
    with patch(SCHEMA_REGISTRY_CLS) as mock:
        sr = _schema_registry_mock(mock)
        avroSerde = AvroKeyValueSerde(sr, TOPIC)
        with pytest.raises(SerializerError) as e:
            avroSerde.value.deserialize(None)


def test_value_deserialize_success(
    employee_schema, employee_avro_wire_format, employee_json_data
):
    with patch(SCHEMA_REGISTRY_CLS) as mock:
        schema_id = 23
        sr = _schema_registry_mock(mock, schema_id, employee_schema)
        avroSerde = AvroKeyValueSerde(sr, TOPIC)
        employee_avro_data = employee_avro_wire_format(schema_id)
        decoded_data = avroSerde.value.deserialize(employee_avro_data)
        assert decoded_data == employee_json_data


def test_value_serialize_incompatible_change(
    employee_schema, employee_avro_wire_format, employee_json_data
):
    with patch(SCHEMA_REGISTRY_CLS) as mock:
        sr = _schema_registry_mock(mock)
        sr.register_schema.side_effect = IncompatibleSchemaVersion({})
        avroSerde = AvroKeyValueSerde(sr, TOPIC)
        with pytest.raises(IncompatibleSchemaVersion):
            avroSerde.value.serialize(employee_json_data, employee_schema)


def test_value_serialize_success(
    employee_schema, employee_avro_wire_format, employee_json_data
):
    with patch(SCHEMA_REGISTRY_CLS) as mock:
        schema_id = 45
        sr = _schema_registry_mock(mock, schema_id, employee_schema)
        avroSerde = AvroKeyValueSerde(sr, TOPIC)
        employee_avro = employee_avro_wire_format(schema_id)
        encoded_data = avroSerde.value.serialize(employee_json_data, employee_schema)
        assert encoded_data == employee_avro
        decoded_data = avroSerde.value.deserialize(encoded_data)
        assert decoded_data == employee_json_data

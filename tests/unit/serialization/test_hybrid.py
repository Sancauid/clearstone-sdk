# tests/unit/serialization/test_hybrid.py

import threading

import numpy as np
import pytest

from clearstone.serialization.hybrid import HybridSerializer, SelectiveSnapshotCapture


class CustomTestClass:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, CustomTestClass) and self.value == other.value


@pytest.fixture
def serializer():
    return HybridSerializer()


def test_json_primitives_roundtrip(serializer):
    """Test that basic JSON-compatible types serialize and deserialize correctly."""
    primitives = [1, "hello", 3.14, True, None, [1, "a"], {"key": "value"}]
    for obj in primitives:
        serialized = serializer.serialize(obj)
        deserialized = serializer.deserialize(serialized)
        assert deserialized == obj
        assert '"__type__": "json"' in serialized


def test_pickle_fallback_for_custom_object(serializer):
    """Test that a custom, non-JSON-serializable object uses pickle."""
    obj = CustomTestClass(value=123)
    serialized = serializer.serialize(obj)
    deserialized = serializer.deserialize(serialized)

    assert '"__type__": "pickle"' in serialized
    assert isinstance(deserialized, CustomTestClass)
    assert deserialized == obj


def test_pickle_fallback_for_numpy_array(serializer):
    """Test that a numpy array correctly uses pickle for serialization."""
    obj = np.array([1, 2, 3])
    serialized = serializer.serialize(obj)
    deserialized = serializer.deserialize(serialized)

    assert '"__type__": "pickle"' in serialized
    assert isinstance(deserialized, np.ndarray)
    assert np.array_equal(deserialized, obj)


def test_deserialization_of_invalid_json_raises_error(serializer):
    """Test that malformed JSON strings raise a ValueError."""
    with pytest.raises(ValueError, match="Invalid JSON format"):
        serializer.deserialize("{not_json:}")


def test_selective_snapshot_capture_success():
    """Test that a small object is captured successfully."""
    obj = {"message": "hello world"}
    snapshot = SelectiveSnapshotCapture.capture(obj)

    assert snapshot["captured"] is True
    assert "data" in snapshot
    serializer = HybridSerializer()
    deserialized = serializer.deserialize(snapshot["data"])
    assert deserialized == obj


def test_selective_snapshot_capture_rejects_large_object():
    """Test that an object exceeding the size limit is not captured."""
    large_string = "a" * (SelectiveSnapshotCapture.DEFAULT_MAX_SIZE_BYTES + 1)
    obj = {"large_data": large_string}

    snapshot = SelectiveSnapshotCapture.capture(obj)

    assert snapshot["captured"] is False
    assert "Snapshot size" in snapshot["reason"]
    assert "data" not in snapshot


def test_selective_snapshot_capture_with_custom_limit():
    """Test that a custom size limit is respected."""
    obj = {"data": "a" * 500}

    small_limit_snapshot = SelectiveSnapshotCapture.capture(obj, max_size_bytes=100)
    assert small_limit_snapshot["captured"] is False

    large_limit_snapshot = SelectiveSnapshotCapture.capture(obj, max_size_bytes=1000)
    assert large_limit_snapshot["captured"] is True


def test_serialization_of_unserializable_object_returns_error(serializer):
    """Test that objects that cannot be pickled are handled gracefully."""
    obj = threading.Lock()
    serialized = serializer.serialize(obj)

    assert '"__type__": "error"' in serialized
    with pytest.raises(ValueError, match="Original object could not be serialized"):
        serializer.deserialize(serialized)

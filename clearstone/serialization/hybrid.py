# clearstone/serialization/hybrid.py

import json
import pickle
import base64
import sys
from typing import Any, Dict
from abc import ABC, abstractmethod

class SerializationStrategy(ABC):
    """Abstract base class for serialization strategies."""
    
    @abstractmethod
    def serialize(self, obj: Any) -> str:
        """Serialize object to a JSON-compatible string."""
        pass
    
    @abstractmethod
    def deserialize(self, data: str) -> Any:
        """Deserialize object from a string."""
        pass

class HybridSerializer(SerializationStrategy):
    """
    Hybrid serialization strategy: Attempts JSON, falls back to pickle.
    This provides a balance of safety, portability, and fidelity.
    """
    
    def serialize(self, obj: Any) -> str:
        """Serializes an object with type tagging for safe deserialization."""
        try:
            json.dumps(obj)
            return json.dumps({
                "__type__": "json",
                "value": obj
            })
        except (TypeError, ValueError):
            try:
                pickled = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
                encoded = base64.b64encode(pickled).decode("utf-8")
                return json.dumps({
                    "__type__": "pickle",
                    "value": encoded,
                    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}"
                })
            except Exception as e:
                return json.dumps({
                    "__type__": "error",
                    "reason": f"Serialization failed: {str(e)}",
                    "obj_type": type(obj).__name__
                })
    
    def deserialize(self, data: str) -> Any:
        """Deserializes data based on the embedded type tag."""
        try:
            container = json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format for deserialization: {e}")
        
        type_tag = container.get("__type__")

        if type_tag == "json":
            return container.get("value")
        
        elif type_tag == "pickle":
            encoded = container.get("value")
            pickled = base64.b64decode(encoded.encode("utf-8"))
            try:
                return pickle.loads(pickled)
            except Exception as e:
                return f"<Pickle Deserialization Error: {str(e)}>"
        
        elif type_tag == "error":
            raise ValueError(f"Original object could not be serialized: {container.get('reason')}")
        
        else:
            raise ValueError(f"Unknown serialization type tag: {type_tag}")

class SelectiveSnapshotCapture:
    """
    A utility for safely capturing snapshots of data for traces, with a
    configurable size limit to prevent storing excessively large objects.
    """
    
    DEFAULT_MAX_SIZE_BYTES = 1 * 1024 * 1024

    @staticmethod
    def capture(obj: Any, max_size_bytes: int = None) -> Dict[str, Any]:
        """
        Captures a snapshot of an object, respecting size limits.

        Returns:
            A dictionary indicating if the capture was successful, and either
            the serialized data or the reason for failure.
        """
        max_size = max_size_bytes or SelectiveSnapshotCapture.DEFAULT_MAX_SIZE_BYTES
        serializer = HybridSerializer()
        
        try:
            serialized_data = serializer.serialize(obj)
            size_bytes = len(serialized_data.encode("utf-8"))

            if size_bytes > max_size:
                return {
                    "captured": False,
                    "reason": f"Snapshot size ({size_bytes} bytes) exceeds limit of {max_size} bytes.",
                    "type": type(obj).__name__,
                }
            
            return {
                "captured": True,
                "data": serialized_data,
                "size_bytes": size_bytes,
            }
        except Exception as e:
            return {
                "captured": False,
                "reason": f"An unexpected error occurred during serialization: {str(e)}",
                "type": type(obj).__name__,
            }


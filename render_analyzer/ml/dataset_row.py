import json
import uuid
import hashlib
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class DatasetRow:
    schema_version: int
    timestamp: str
    blender_version: str
    addon_version: str
    render_id: str
    metadata: Dict[str, Any]
    feature_hash: str
    features: Dict[str, float]
    target: Optional[Dict[str, float]] = None

    @classmethod
    def compute_feature_hash(cls, features: Dict[str, float], feature_order: tuple) -> str:
        """
        Computes a SHA-256 hash of the serialized, strictly ordered feature dictionary.
        This detects duplicate exports, corruption, and schema drift.
        """
        ordered_features = {k: features[k] for k in feature_order}
        serialized = json.dumps(ordered_features, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

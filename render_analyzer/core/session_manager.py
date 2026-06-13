from typing import Optional, Dict, Any

class AnalysisSession:
    """
    Single source of truth for the latest active analysis session.
    Stores the snapshot and feature vector independently of Blender's scene data
    to prevent loss during cache invalidations or reloads.
    """
    latest_snapshot: Any = None  # Typed as Any to avoid circular imports. Expects SceneAnalysisSnapshot.
    latest_feature_vector: Optional[Dict[str, float]] = None

    @classmethod
    def set_snapshot(cls, snapshot):
        cls.latest_snapshot = snapshot

    @classmethod
    def get_snapshot(cls):
        return cls.latest_snapshot

    @classmethod
    def set_feature_vector(cls, vector: Dict[str, float]):
        cls.latest_feature_vector = vector

    @classmethod
    def get_feature_vector(cls) -> Optional[Dict[str, float]]:
        return cls.latest_feature_vector

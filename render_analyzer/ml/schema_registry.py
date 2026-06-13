from .feature_schema import FEATURES_V1, FEATURE_ORDER_V1

SCHEMA_REGISTRY = {
    1: {
        "features": FEATURES_V1,
        "order": FEATURE_ORDER_V1
    }
}

CURRENT_SCHEMA_VERSION = 1

def get_schema(version: int = CURRENT_SCHEMA_VERSION) -> dict:
    if version not in SCHEMA_REGISTRY:
        raise ValueError(f"Unknown schema version: {version}")
    return SCHEMA_REGISTRY[version]

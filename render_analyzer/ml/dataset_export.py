import json
import dataclasses
import logging
from pathlib import Path
from .dataset_row import DatasetRow
from .dataset_manager import DatasetManager

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.DEBUG)
DEBUG_BENCHMARK_PIPELINE = True

def append_jsonl_row(row: DatasetRow):
    """Appends a DatasetRow to the JSONL dataset file securely."""
    if not DatasetManager.validate_features(row.features, row.schema_version):
        raise ValueError("Feature validation failed. Schema mismatch or invalid values.")
        
    if row.features.get("benchmark_time", 0.0) > 0.0:
        if DEBUG_BENCHMARK_PIPELINE:
            logger.debug(f"EXPORT BENCHMARK: time={row.features.get('benchmark_time')}")
        
    path = DatasetManager.get_dataset_path(row.schema_version)
    
    row_dict = dataclasses.asdict(row)
    json_str = json.dumps(row_dict, separators=(',', ':'))
    
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json_str + "\n")

def export_dataset_row(row: DatasetRow, filename: str = "scene_features.json") -> Path:
    """Exports a single DatasetRow to a pretty-printed JSON file."""
    if not DatasetManager.validate_features(row.features, row.schema_version):
        raise ValueError("Feature validation failed. Schema mismatch or invalid values.")
        
    if row.features.get("benchmark_time", 0.0) > 0.0:
        if DEBUG_BENCHMARK_PIPELINE:
            logger.debug(f"EXPORT BENCHMARK: time={row.features.get('benchmark_time')}")
        
    path = DatasetManager.get_exports_dir() / filename
    
    row_dict = dataclasses.asdict(row)
    json_str = json.dumps(row_dict, indent=2)
    
    # Write atomically
    temp_path = path.with_suffix(".tmp")
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(json_str)
    
    temp_path.replace(path)
    
    # Also export feature summary
    export_feature_summary(row.schema_version)
    
    return path

import datetime
from .schema_registry import get_schema, CURRENT_SCHEMA_VERSION

def export_feature_summary(schema_version: int = CURRENT_SCHEMA_VERSION) -> Path:
    """Exports a summary of the dataset schema to a JSON file."""
    schema_info = get_schema(schema_version)
    feature_names = list(schema_info["features"].keys())
    
    summary = {
        "schema_version": schema_version,
        "feature_count": len(feature_names),
        "feature_names": feature_names,
        "export_timestamp": datetime.datetime.now().isoformat()
    }
    
    path = DatasetManager.get_exports_dir() / "feature_summary.json"
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
        
    return path

import json
import dataclasses
from pathlib import Path
from .dataset_row import DatasetRow
from .dataset_manager import DatasetManager

def append_jsonl_row(row: DatasetRow):
    """Appends a DatasetRow to the JSONL dataset file securely."""
    if not DatasetManager.validate_features(row.features, row.schema_version):
        raise ValueError("Feature validation failed. Schema mismatch or invalid values.")
        
    path = DatasetManager.get_dataset_path(row.schema_version)
    
    row_dict = dataclasses.asdict(row)
    json_str = json.dumps(row_dict, separators=(',', ':'))
    
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json_str + "\n")

def export_dataset_row(row: DatasetRow, filename: str = "scene_features.json") -> Path:
    """Exports a single DatasetRow to a pretty-printed JSON file."""
    if not DatasetManager.validate_features(row.features, row.schema_version):
        raise ValueError("Feature validation failed. Schema mismatch or invalid values.")
        
    path = DatasetManager.get_exports_dir() / filename
    
    row_dict = dataclasses.asdict(row)
    json_str = json.dumps(row_dict, indent=2)
    
    # Write atomically
    temp_path = path.with_suffix(".tmp")
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(json_str)
    
    temp_path.replace(path)
    return path

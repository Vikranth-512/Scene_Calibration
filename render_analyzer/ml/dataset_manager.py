import os
import json
import math
from pathlib import Path
from typing import Dict, Any
from .schema_registry import get_schema, CURRENT_SCHEMA_VERSION
from .dataset_row import DatasetRow

class DatasetManager:
    @staticmethod
    def get_dataset_dir() -> Path:
        p = Path.home() / "RenderAnalyzer" / "datasets"
        p.mkdir(parents=True, exist_ok=True)
        return p
        
    @staticmethod
    def get_exports_dir() -> Path:
        p = Path.home() / "RenderAnalyzer" / "exports"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @staticmethod
    def get_dataset_path(schema_version: int = CURRENT_SCHEMA_VERSION) -> Path:
        return DatasetManager.get_dataset_dir() / f"dataset_v{schema_version}.jsonl"

    @staticmethod
    def validate_features(features: Dict[str, float], schema_version: int = CURRENT_SCHEMA_VERSION) -> bool:
        schema_info = get_schema(schema_version)
        schema_features = schema_info["features"]
        
        if len(features) != len(schema_features):
            missing = set(schema_features.keys()) - set(features.keys())
            extra = set(features.keys()) - set(schema_features.keys())
            print(f"RenderAnalyzer Validation: key count mismatch. "
                  f"Schema expects {len(schema_features)}, got {len(features)}.")
            if missing:
                print(f"  Missing keys: {missing}")
            if extra:
                print(f"  Extra keys: {extra}")
            return False
            
        if sorted(features.keys()) != sorted(schema_features.keys()):
            missing = set(schema_features.keys()) - set(features.keys())
            extra = set(features.keys()) - set(schema_features.keys())
            print(f"RenderAnalyzer Validation: key name mismatch.")
            if missing:
                print(f"  Missing keys: {missing}")
            if extra:
                print(f"  Extra keys: {extra}")
            return False
            
        for k, v in features.items():
            if not isinstance(v, (int, float)):
                print(f"RenderAnalyzer Validation: feature '{k}' has non-numeric value: {v} ({type(v).__name__})")
                return False
            if not math.isfinite(v):
                print(f"RenderAnalyzer Validation: feature '{k}' is not finite: {v}")
                return False
                
        # Semantic consistency warnings (non-blocking)
        if features.get("texture_count", 0.0) > 0.0:
            if features.get("texture_memory_mb", 0.0) <= 0.0:
                print("RenderAnalyzer Validation WARNING: texture_count > 0 but texture_memory_mb <= 0. "
                      "Re-analyze the scene to fix texture data.")
                
        # Backend validation (blocking)
        backends = ["backend_cpu", "backend_cuda", "backend_optix", "backend_hip", "backend_metal"]
        b_sum = sum(features.get(b, 0.0) for b in backends)
        if abs(b_sum - 1.0) > 1e-5:
            print(f"RenderAnalyzer Validation failed: exactly one backend must be active, got sum {b_sum}")
            return False
                
        return True

    @staticmethod
    def get_stats(schema_version: int = CURRENT_SCHEMA_VERSION) -> Dict[str, Any]:
        path = DatasetManager.get_dataset_path(schema_version)
        if not path.exists():
            return {
                "row_count": 0,
                "schema_version": schema_version,
                "last_write": None
            }
            
        row_count = 0
        last_write = os.path.getmtime(path)
        
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    row_count += 1
                    
        return {
            "row_count": row_count,
            "schema_version": schema_version,
            "last_write": last_write
        }

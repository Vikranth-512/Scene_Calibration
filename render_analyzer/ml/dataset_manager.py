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
    def _validate_one_hot(features: Dict[str, float], group_name: str, keys: list, blocking: bool = True) -> bool:
        """Validate that exactly one feature in a one-hot group equals 1.0."""
        total = sum(features.get(k, 0.0) for k in keys)
        if abs(total - 1.0) > 1e-5:
            msg = (f"RenderAnalyzer Validation {'FAILED' if blocking else 'WARNING'}: "
                   f"{group_name} one-hot sum must be 1, got {total}. "
                   f"Values: {{{', '.join(f'{k}={features.get(k, 0.0)}' for k in keys)}}}")
            print(msg)
            return not blocking
        return True

    @staticmethod
    def validate_features(features: Dict[str, float], schema_version: int = CURRENT_SCHEMA_VERSION) -> bool:
        schema_info = get_schema(schema_version)
        schema_features = schema_info["features"]
        
        # Key name and order check
        expected_keys = list(schema_features.keys())
        actual_keys = list(features.keys())
        
        if actual_keys != expected_keys:
            if set(actual_keys) != set(expected_keys):
                missing = set(expected_keys) - set(actual_keys)
                extra = set(actual_keys) - set(expected_keys)
                raise ValueError(f"RenderAnalyzer Validation: key mismatch. Missing: {missing}, Extra: {extra}")
            else:
                for i, (e, a) in enumerate(zip(expected_keys, actual_keys)):
                    if e != a:
                        raise ValueError(f"RenderAnalyzer Validation: key order mismatch at index {i}. Expected '{e}', got '{a}'.")
            
        # Type and finiteness check
        for k, v in features.items():
            if v is None:
                raise ValueError(f"RenderAnalyzer Validation: feature '{k}' is None")
            if not isinstance(v, (int, float)):
                raise ValueError(f"RenderAnalyzer Validation: feature '{k}' has non-numeric value: {v} ({type(v).__name__})")
            if not math.isfinite(v):
                raise ValueError(f"RenderAnalyzer Validation: feature '{k}' is not finite: {v}")
                
        # === Semantic consistency warnings (non-blocking) ===
        if features.get("texture_count", 0.0) > 0.0:
            if features.get("texture_memory_mb", 0.0) <= 0.0:
                print("RenderAnalyzer Validation WARNING: texture_count > 0 but texture_memory_mb <= 0. "
                      "Re-analyze the scene to fix texture data.")
                
        # === One-hot validation (blocking) ===
        
        # Backend: exactly one must be active
        if not DatasetManager._validate_one_hot(features, "Backend",
            ["backend_cpu", "backend_cuda", "backend_optix", "backend_hip", "backend_metal"]):
            return False
            
        # Render Device: exactly one must be active
        if not DatasetManager._validate_one_hot(features, "Render Device",
            ["render_device_gpu", "render_device_cpu"]):
            return False
            
        # GPU Vendor: exactly one must be active
        if not DatasetManager._validate_one_hot(features, "GPU Vendor",
            ["gpu_vendor_nvidia", "gpu_vendor_amd", "gpu_vendor_intel", "gpu_vendor_apple", "gpu_vendor_unknown"]):
            return False
            
        # GPU Family: exactly one must be active
        if not DatasetManager._validate_one_hot(features, "GPU Family",
            ["gpu_family_gtx", "gpu_family_rtx", "gpu_family_quadro", "gpu_family_tesla",
             "gpu_family_rx", "gpu_family_arc", "gpu_family_integrated", "gpu_family_unknown"]):
            return False
        
        # === Capability consistency warnings (non-blocking) ===
        capability_backend_pairs = [
            ("capability_optix", "backend_optix"),
            ("capability_cuda", "backend_cuda"),
            ("capability_hip", "backend_hip"),
            ("capability_metal", "backend_metal"),
        ]
        for cap_key, backend_key in capability_backend_pairs:
            if features.get(backend_key, 0.0) == 1.0 and features.get(cap_key, 0.0) == 0.0:
                print(f"RenderAnalyzer Validation WARNING: {backend_key}=1 but {cap_key}=0. "
                      f"Backend is active without detected capability.")
                
        return True

    @staticmethod
    def get_stats(schema_version: int = CURRENT_SCHEMA_VERSION) -> Dict[str, Any]:
        path = DatasetManager.get_dataset_path(schema_version)
        schema_info = get_schema(schema_version)
        feature_count = len(schema_info["features"])

        if not path.exists():
            return {
                "row_count": 0,
                "schema_version": schema_version,
                "feature_count": feature_count,
                "dataset_size_mb": 0.0,
                "last_write": None
            }
            
        row_count = 0
        last_write = os.path.getmtime(path)
        dataset_size_mb = os.path.getsize(path) / (1024 * 1024)
        
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    row_count += 1
                    
        return {
            "row_count": row_count,
            "schema_version": schema_version,
            "feature_count": feature_count,
            "dataset_size_mb": round(dataset_size_mb, 2),
            "last_write": last_write
        }

import bpy
import time
import uuid
import datetime
from .schema_registry import CURRENT_SCHEMA_VERSION, get_schema
from .dataset_row import DatasetRow
from .feature_extractor import FeatureExtractor
from .dataset_export import append_jsonl_row
from ..core.session_manager import AnalysisSession

_pending_telemetry_rows = {}
_render_start_times = {}

@bpy.app.handlers.persistent
def ml_telemetry_render_init(scene):
    if not getattr(scene, "render_analyzer_props", None) or not scene.render_analyzer_props.enable_ml_telemetry:
        return
        
    snapshot = AnalysisSession.get_snapshot()
    if not snapshot:
        # We cannot generate a row without a prior analysis
        return
        
    # Generate Render ID
    render_id = str(uuid.uuid4())
    _render_start_times[render_id] = time.time()
    
    # We must store the render_id in the scene so render_complete knows which one finished.
    scene["_ml_telemetry_render_id"] = render_id
    
    # Hardware metadata
    hardware = getattr(snapshot, "hardware", None)
    
    # Try to get samples depending on engine
    samples = 0
    if scene.render.engine == 'CYCLES':
        samples = scene.cycles.samples
    elif scene.render.engine == 'BLENDER_EEVEE_NEXT':
        samples = scene.eevee.taa_render_samples
        
    metadata = {
        "gpu_name": hardware.gpu_names[0] if hardware and hardware.gpu_names else "Unknown",
        "cpu_name": hardware.cpu_name if hardware else "Unknown",
        "blender_version": ".".join(map(str, bpy.app.version)),
        "addon_version": "1.0.0", 
        "samples": samples,
        "resolution_x": scene.render.resolution_x,
        "resolution_y": scene.render.resolution_y,
        "engine": scene.render.engine
    }
    
    features = FeatureExtractor.extract(snapshot, CURRENT_SCHEMA_VERSION)
    schema_info = get_schema(CURRENT_SCHEMA_VERSION)
    feature_hash = DatasetRow.compute_feature_hash(features, schema_info["order"])
    
    row = DatasetRow(
        schema_version=CURRENT_SCHEMA_VERSION,
        timestamp=datetime.datetime.now().isoformat(),
        blender_version=metadata["blender_version"],
        addon_version=metadata["addon_version"],
        render_id=render_id,
        metadata=metadata,
        feature_hash=feature_hash,
        features=features
    )
    
    _pending_telemetry_rows[render_id] = row


@bpy.app.handlers.persistent
def ml_telemetry_render_complete(scene):
    if not getattr(scene, "render_analyzer_props", None) or not scene.render_analyzer_props.enable_ml_telemetry:
        return
        
    render_id = scene.get("_ml_telemetry_render_id")
    if not render_id or render_id not in _pending_telemetry_rows:
        return
        
    start_time = _render_start_times.pop(render_id, None)
    row = _pending_telemetry_rows.pop(render_id)
    
    if start_time is None:
        return
        
    end_time = time.time()
    actual_render_time_seconds = end_time - start_time
    
    row.target = {
        "actual_render_time_seconds": float(actual_render_time_seconds)
    }
    
    try:
        append_jsonl_row(row)
    except Exception as e:
        print(f"ML Telemetry Export Failed: {e}")

def register_ml_telemetry():
    if ml_telemetry_render_init not in bpy.app.handlers.render_init:
        bpy.app.handlers.render_init.append(ml_telemetry_render_init)
    if ml_telemetry_render_complete not in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.append(ml_telemetry_render_complete)

def unregister_ml_telemetry():
    if ml_telemetry_render_init in bpy.app.handlers.render_init:
        bpy.app.handlers.render_init.remove(ml_telemetry_render_init)
    if ml_telemetry_render_complete in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(ml_telemetry_render_complete)

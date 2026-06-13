import bpy
import datetime
import uuid
from ..core.session_manager import AnalysisSession
from ..ml.feature_extractor import FeatureExtractor
from ..ml.dataset_row import DatasetRow
from ..ml.schema_registry import CURRENT_SCHEMA_VERSION, get_schema
from ..ml.dataset_export import export_dataset_row

class RENDERANALYZER_OT_export_ml_features(bpy.types.Operator):
    """Export features from the latest analysis to a JSON file"""
    bl_idname = "renderanalyzer.export_ml_features"
    bl_label = "Export ML Features"
    bl_options = {'REGISTER'}

    def execute(self, context):
        snapshot = AnalysisSession.get_snapshot()
        if not snapshot:
            self.report({'WARNING'}, "Render Analyzer: No active snapshot. Please Analyze Scene first.")
            return {'CANCELLED'}
            
        features = FeatureExtractor.extract(snapshot, CURRENT_SCHEMA_VERSION)
        schema_info = get_schema(CURRENT_SCHEMA_VERSION)
        feature_hash = DatasetRow.compute_feature_hash(features, schema_info["order"])
        
        hardware = getattr(snapshot, "hardware", None)
        metadata = {
            "gpu_name": hardware.gpu_names[0] if hardware and hardware.gpu_names else "Unknown",
            "cpu_name": hardware.cpu_name if hardware else "Unknown",
            "blender_version": ".".join(map(str, bpy.app.version)),
            "addon_version": "1.0.0", 
            "samples": context.scene.cycles.samples if context.scene.render.engine == 'CYCLES' else context.scene.eevee.taa_render_samples,
            "resolution_x": context.scene.render.resolution_x,
            "resolution_y": context.scene.render.resolution_y,
            "engine": context.scene.render.engine
        }
        
        row = DatasetRow(
            schema_version=CURRENT_SCHEMA_VERSION,
            timestamp=datetime.datetime.now().isoformat(),
            blender_version=metadata["blender_version"],
            addon_version=metadata["addon_version"],
            render_id=str(uuid.uuid4()),
            metadata=metadata,
            feature_hash=feature_hash,
            features=features
        )
        
        try:
            path = export_dataset_row(row)
            self.report({'INFO'}, f"Render Analyzer: Exported ML features to {path}")
        except Exception as e:
            self.report({'ERROR'}, f"Render Analyzer: Failed to export ML features: {e}")
            return {'CANCELLED'}
            
        return {'FINISHED'}

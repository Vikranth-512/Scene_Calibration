import bpy
from ..utils.scene_cache import load_analysis_from_cache, save_analysis_to_cache, generate_scene_fingerprint
from ..utils.statistics import SceneAnalysisSnapshot
from ..analyzers.hardware_analyzer import analyze_hardware
from ..analyzers.scene_analyzer import analyze_scene
from ..analyzers.mesh_analyzer import analyze_meshes
from ..analyzers.texture_analyzer import analyze_textures
from ..analyzers.material_analyzer import analyze_materials
from ..analyzers.lighting_analyzer import analyze_lighting
from ..analyzers.volume_analyzer import analyze_volumes
from ..analyzers.render_settings_analyzer import analyze_render_settings
from ..estimation.complexity_score import calculate_scores
from ..estimation.memory_estimator import estimate_memory
from ..estimation.render_time_estimator import RuleBasedEstimator

class RENDERANALYZER_OT_analyze_scene(bpy.types.Operator):
    """Analyze the current scene for performance bottlenecks"""
    bl_idname = "renderanalyzer.analyze_scene"
    bl_label = "Analyze Scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        
        # Check cache
        cached = load_analysis_from_cache(scene)
        if cached:
            self.report({'INFO'}, "Render Analyzer: Loaded from cache.")
            scene.render_analyzer_props.update_from_snapshot(cached)
            
            # Estimate Time
            benchmark_data = context.scene.render_analyzer_props.benchmark_data
            
            estimator = RuleBasedEstimator()
            est_result = estimator.estimate(cached, benchmark_data_json=benchmark_data)
            
            context.scene.render_analyzer_props.estimated_frame_time_s = est_result.estimated_frame_time_seconds
            context.scene.render_analyzer_props.confidence_score = est_result.confidence_score
            
            return {'FINISHED'}
            
        self.report({'INFO'}, "Render Analyzer: Analyzing scene...")
        
        snapshot = SceneAnalysisSnapshot()
        
        # 1. Hardware
        snapshot.hardware = analyze_hardware()
        
        # 2. Extract Data
        depsgraph = context.evaluated_depsgraph_get()
        snapshot.scene_stats = analyze_scene()
        mode = scene.render_analyzer_props.analysis_mode
        meshes, instances = analyze_meshes(depsgraph, mode=mode)
        snapshot.top_textures = analyze_textures()
        materials = analyze_materials(scene)
        lighting = analyze_lighting()
        volumes = analyze_volumes()
        snapshot.render_settings = analyze_render_settings()
        
        # 3. Calculate Scores & Memory
        snapshot.instances = instances
        snapshot.cycles_score, snapshot.eevee_score, snapshot.top_bottlenecks = calculate_scores(
            meshes, instances, materials, lighting, volumes, snapshot.render_settings, instance_multiplier=0.15
        )
        snapshot.memory_estimate = estimate_memory(meshes, snapshot.top_textures, volumes)
        
        # Estimate Time
        benchmark_data = context.scene.render_analyzer_props.benchmark_data
        
        estimator = RuleBasedEstimator()
        est_result = estimator.estimate(snapshot, benchmark_data_json=benchmark_data)
        
        scene.render_analyzer_props.estimated_frame_time_s = est_result.estimated_frame_time_seconds
        scene.render_analyzer_props.confidence_score = est_result.confidence_score
        
        # 4. Save Cache
        save_analysis_to_cache(scene, snapshot)
        
        # 5. Update UI Props
        scene.render_analyzer_props.update_from_snapshot(snapshot)
        
        self.report({'INFO'}, "Render Analyzer: Analysis complete.")
        return {'FINISHED'}

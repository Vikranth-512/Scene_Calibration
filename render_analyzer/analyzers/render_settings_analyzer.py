import bpy
from ..utils.statistics import RenderSettingsStats

def analyze_render_settings() -> RenderSettingsStats:
    stats = RenderSettingsStats()
    scene = bpy.context.scene
    
    stats.engine = scene.render.engine
    stats.resolution_x = scene.render.resolution_x
    stats.resolution_y = scene.render.resolution_y
    stats.resolution_percentage = scene.render.resolution_percentage
    
    if stats.engine == 'CYCLES':
        stats.samples = scene.cycles.samples
        stats.adaptive_sampling = scene.cycles.use_adaptive_sampling
        stats.max_bounces = scene.cycles.max_bounces
        stats.diffuse_bounces = scene.cycles.diffuse_bounces
        stats.glossy_bounces = scene.cycles.glossy_bounces
        stats.transmission_bounces = scene.cycles.transmission_bounces
        stats.caustics_reflective = scene.cycles.caustics_reflective
        stats.caustics_refractive = scene.cycles.caustics_refractive
        stats.denoising = scene.cycles.use_denoising
    elif stats.engine == 'BLENDER_EEVEE':
        # Eevee Next in 4.2+ has slightly different settings, try safe fallback
        stats.samples = getattr(scene.eevee, "taa_render_samples", 64)
        
    stats.motion_blur = scene.render.use_motion_blur
    
    # Depth of field is per camera, check active
    if scene.camera and scene.camera.data:
        stats.depth_of_field = scene.camera.data.dof.use_dof

    # Calculate basic cost score
    cost = 0
    if stats.engine == 'CYCLES':
        cost += stats.samples * 0.1
        cost += stats.max_bounces * 2
        if stats.caustics_reflective or stats.caustics_refractive:
            cost += 20
        if stats.denoising:
            cost += 10
        if stats.motion_blur:
            cost += 30
        if stats.depth_of_field:
            cost += 20
    elif stats.engine == 'BLENDER_EEVEE':
        cost += stats.samples * 0.05
        if stats.motion_blur:
            cost += 15
        if stats.depth_of_field:
            cost += 10
            
    stats.render_settings_cost_score = int(cost)
    return stats

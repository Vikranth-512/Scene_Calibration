from typing import List, Tuple
from ..utils.statistics import (
    CyclesComplexityScore, EeveeComplexityScore, MeshStats, 
    MaterialStats, LightingStats, VolumeStats, RenderSettingsStats,
    ObjectBottleneck
)

def determine_category(score: float) -> str:
    if score < 20: return "Very Light"
    if score < 40: return "Light"
    if score < 60: return "Moderate"
    if score < 80: return "Heavy"
    return "Extreme"

def calculate_scores(
    meshes: List[MeshStats],
    materials: List[MaterialStats],
    lighting: LightingStats,
    volumes: VolumeStats,
    render_settings: RenderSettingsStats
) -> Tuple[CyclesComplexityScore, EeveeComplexityScore, List[ObjectBottleneck]]:
    
    cycles = CyclesComplexityScore()
    eevee = EeveeComplexityScore()
    
    # 1. Base Mesh Score
    total_faces = sum(m.face_count for m in meshes)
    # Simple heuristic: 1 million faces = 20 points
    base_mesh_points = min((total_faces / 1_000_000.0) * 20, 100)
    
    cycles.mesh_score = base_mesh_points
    eevee.mesh_score = base_mesh_points * 1.5 # Eevee struggles more with raw huge poly counts due to VRAM
    
    # 2. Shader Score
    total_shader_cost = sum(m.shader_complexity_score for m in materials)
    cycles.shader_score = min((total_shader_cost / 1000.0) * 20, 100)
    eevee.shader_score = min((total_shader_cost / 800.0) * 20, 100)
    
    # 3. Lighting Score
    cycles.lighting_score = min((lighting.lighting_cost_score / 200.0) * 15, 100)
    eevee.lighting_score = min((lighting.lighting_cost_score / 100.0) * 30, 100) # Shadow maps in Eevee are expensive
    
    # 4. Volume Score
    # Volumes are extremely expensive in Cycles, moderate in Eevee
    cycles.volume_score = min((volumes.volumetric_cost_score / 200.0) * 30, 100)
    eevee.volume_score = min((volumes.volumetric_cost_score / 300.0) * 15, 100)
    
    # 5. Render Settings Score
    cycles.render_settings_score = min((render_settings.render_settings_cost_score / 150.0) * 15, 100)
    eevee.render_settings_score = min((render_settings.render_settings_cost_score / 100.0) * 10, 100)
    
    # Calculate Total
    cycles.total_score = min(cycles.mesh_score + cycles.shader_score + cycles.lighting_score + cycles.volume_score + cycles.render_settings_score, 100.0)
    eevee.total_score = min(eevee.mesh_score + eevee.shader_score + eevee.lighting_score + eevee.volume_score + eevee.render_settings_score, 100.0)
    
    cycles.category = determine_category(cycles.total_score)
    eevee.category = determine_category(eevee.total_score)
    
    # --- Bottleneck Calculation ---
    bottlenecks = []
    for m in meshes:
        impact = 0.0
        cause = []
        
        if m.face_count > 500_000:
            impact += 40
            cause.append("High Poly Count")
        elif m.face_count > 100_000:
            impact += 20
            cause.append("Moderate Poly Count")
            
        if m.has_geometry_nodes:
            impact += 30
            cause.append("Geometry Nodes")
            
        if m.has_subdivision:
            impact += 20
            cause.append("Subdivision")
            
        # Simplified material matching (assume expensive material is attached)
        # Real implementation would trace exact slots
        
        if impact > 0:
            bottlenecks.append(ObjectBottleneck(
                object_name=m.object_name,
                impact_score=impact,
                primary_cause=", ".join(cause)
            ))
            
    bottlenecks.sort(key=lambda b: b.impact_score, reverse=True)
    
    # Calculate percentages for top 20
    top_20 = bottlenecks[:20]
    total_impact = sum(b.impact_score for b in top_20) if top_20 else 1.0
    for b in top_20:
        b.contribution_percent = (b.impact_score / total_impact) * 100.0
        
    return cycles, eevee, top_20

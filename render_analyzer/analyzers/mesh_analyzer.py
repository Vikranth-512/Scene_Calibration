import bpy
from typing import Tuple, List, Dict
from ..utils.statistics import MeshStats, InstanceStats
from ..utils.helpers import get_evaluated_mesh, free_evaluated_mesh
import hashlib

OBJECT_ANALYSIS_CACHE = {}

def get_object_fingerprint(obj):
    """Fast fingerprint of an object's local geometry-affecting state."""
    fp = hashlib.md5()
    
    # Fast base approximations
    if obj.data and hasattr(obj.data, 'vertices'):
        fp.update(str(len(obj.data.vertices)).encode('utf-8'))
        fp.update(str(len(obj.data.polygons)).encode('utf-8'))
        
    fp.update(str(len(obj.modifiers)).encode('utf-8'))
    
    # If the object is driven or has shape keys, it's highly dynamic. We'll hash the frame too.
    if obj.animation_data and obj.animation_data.drivers:
        fp.update(str(bpy.context.scene.frame_current).encode('utf-8'))
    elif hasattr(obj.data, "shape_keys") and obj.data.shape_keys and obj.data.shape_keys.animation_data:
        fp.update(str(bpy.context.scene.frame_current).encode('utf-8'))
        
    return fp.hexdigest()

def analyze_meshes(depsgraph, mode='BALANCED') -> Tuple[List[MeshStats], List[InstanceStats]]:
    mesh_stats_list = []
    
    instance_counts: Dict[str, int] = {}
    base_object_refs: Dict[str, bpy.types.Object] = {}
    # 1. Traverse all object instances in the depsgraph
    for instance in depsgraph.object_instances:
        obj = instance.object
        
        # We only care about objects that can render as geometry
        if obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
            continue
            
        obj_name = obj.name
        
        # Count instances
        if instance.is_instance:
            instance_counts[obj_name] = instance_counts.get(obj_name, 0) + 1
            if obj_name not in base_object_refs:
                base_object_refs[obj_name] = obj
        
        # Determine cache key
        obj_key = (obj.as_pointer(), get_object_fingerprint(obj), mode)
        
        # If we haven't evaluated this base object's geometry yet, do it now
        if obj_key not in OBJECT_ANALYSIS_CACHE and not instance.is_instance:
            stats = MeshStats()
            stats.object_name = obj_name
            
            # Check modifiers
            stats.has_modifiers = len(obj.modifiers) > 0
            stats.has_subdivision = any(m.type == 'SUBSURF' for m in obj.modifiers)
            stats.has_geometry_nodes = any(m.type == 'NODES' for m in obj.modifiers)
            # Base face count (before evaluation)
            if obj.data and hasattr(obj.data, 'polygons'):
                stats.base_face_count = len(obj.data.polygons)
                
            # Mode Check - FAST vs BALANCED vs DEEP
            if mode == 'FAST' and stats.has_geometry_nodes:
                # User constraint: skip evaluation but label as approximate
                # We do NOT try to guess amplification mathematically. We just pass it through with a warning flag.
                stats.vertex_count = len(obj.data.vertices) if hasattr(obj.data, 'vertices') else 0
                stats.edge_count = len(obj.data.edges) if hasattr(obj.data, 'edges') else 0
                stats.face_count = stats.base_face_count
                stats.evaluated_face_count = stats.base_face_count
                stats.amplification_ratio = 1.0
                stats.triangle_count = stats.base_face_count * 2
                stats.ngon_count = 0
            else:
                mesh = get_evaluated_mesh(obj, depsgraph)
                if mesh:
                    stats.vertex_count = len(mesh.vertices)
                    stats.edge_count = len(mesh.edges)
                    stats.face_count = len(mesh.polygons)
                    stats.evaluated_face_count = len(mesh.polygons)
                    stats.amplification_ratio = stats.evaluated_face_count / max(1, stats.base_face_count)
                    
                    # Count triangles and ngons
                    tri_count = 0
                    ngon_count = 0
                    for poly in mesh.polygons:
                        nv = poly.loop_total
                        if nv == 3:
                            tri_count += 1
                        elif nv == 4:
                            tri_count += 2
                        else:
                            ngon_count += 1
                            tri_count += nv - 2
                            
                    stats.triangle_count = tri_count
                    stats.ngon_count = ngon_count
                    
                    free_evaluated_mesh(obj.evaluated_get(depsgraph), mesh)
            
            # Scoring logic will be handled later or here
            # Simple heuristic score for base geometry
            if stats.face_count > 500000:
                stats.complexity_score = "Extreme"
            elif stats.face_count > 100000:
                stats.complexity_score = "High"
            elif stats.face_count > 10000:
                stats.complexity_score = "Moderate"
            else:
                stats.complexity_score = "Low"
                
            OBJECT_ANALYSIS_CACHE[obj_key] = stats
            
        if not instance.is_instance:
            # We must return the stats from cache
            mesh_stats_list.append(OBJECT_ANALYSIS_CACHE[obj_key])

    # 2. Build InstanceStats
    instance_stats_list = []
    for name, count in instance_counts.items():
        i_stat = InstanceStats()
        i_stat.base_object_name = name
        i_stat.instance_count = count
        
        # We need the key of the base object to lookup its stats
        obj = base_object_refs[name]
        obj_key = (obj.as_pointer(), get_object_fingerprint(obj), mode)
        
        # Calculate total instanced faces if base object was evaluated
        if obj_key in OBJECT_ANALYSIS_CACHE:
            base_stats = OBJECT_ANALYSIS_CACHE[obj_key]
            i_stat.total_instanced_faces = base_stats.face_count * count
            # Tag the base stats as having instances
            base_stats.is_instanced = True
        else:
            # If base wasn't in the view layer directly but instanced
            mesh = get_evaluated_mesh(obj, depsgraph)
            faces = len(mesh.polygons) if mesh else 0
            i_stat.total_instanced_faces = faces * count
            if mesh:
                free_evaluated_mesh(obj.evaluated_get(depsgraph), mesh)
                
        instance_stats_list.append(i_stat)

    return mesh_stats_list, instance_stats_list

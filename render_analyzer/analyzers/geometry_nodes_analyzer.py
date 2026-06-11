import bpy

def analyze_geometry_nodes():
    """
    Informational analyzer for Geometry Nodes setups.
    True geometry cost is captured via the depsgraph evaluated mesh.
    """
    gn_counts = 0
    realize_instances_counts = 0
    
    for obj in bpy.context.scene.objects:
        has_gn = False
        for mod in obj.modifiers:
            if mod.type == 'NODES' and mod.node_group:
                has_gn = True
                # Look for expensive nodes like Realize Instances
                for node in mod.node_group.nodes:
                    if node.type == 'GEOMETRY_NODE_REALIZE_INSTANCES':
                        realize_instances_counts += 1
                        
        if has_gn:
            gn_counts += 1
            
    return {"gn_objects": gn_counts, "realize_instances_nodes": realize_instances_counts}

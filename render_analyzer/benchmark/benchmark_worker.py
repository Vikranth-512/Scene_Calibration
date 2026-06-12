import bpy
import sys
import json
import time

def main():
    # Parse arguments after '--'
    if '--' not in sys.argv:
        print("Error: Expected '--' followed by output JSON path.")
        sys.exit(1)
        
    args = sys.argv[sys.argv.index('--') + 1:]
    if len(args) < 1:
        print("Error: Missing output JSON path.")
        sys.exit(1)
        
    output_path = args[0]
    
    scene = bpy.context.scene
    
    # Save original settings
    original_settings = {
        "use_border": scene.render.use_border,
        "border_min_x": scene.render.border_min_x,
        "border_max_x": scene.render.border_max_x,
        "border_min_y": scene.render.border_min_y,
        "border_max_y": scene.render.border_max_y,
        "use_crop_to_border": scene.render.use_crop_to_border,
        "samples": scene.cycles.samples if scene.render.engine == 'CYCLES' else getattr(scene.eevee, "taa_render_samples", 64),
        "use_persistent_data": scene.render.use_persistent_data if hasattr(scene.render, "use_persistent_data") else False
    }
    
    # Enable persistent data to cache BVH/textures across the 3 renders
    if hasattr(scene.render, "use_persistent_data"):
        scene.render.use_persistent_data = True
    
    regions = [
        (0.389, 0.611, 0.389, 0.611, 0.05),
        (0.342, 0.658, 0.342, 0.658, 0.10),
        (0.276, 0.724, 0.276, 0.724, 0.20),
    ]
    
    results = []
    
    try:
        for r in regions:
            # Apply border
            scene.render.use_border = True
            scene.render.use_crop_to_border = False
            scene.render.border_min_x = r[0]
            scene.render.border_max_x = r[1]
            scene.render.border_min_y = r[2]
            scene.render.border_max_y = r[3]
            
            # Lower samples for benchmark
            if scene.render.engine == 'CYCLES':
                scene.cycles.samples = 16
            else:
                try:
                    scene.eevee.taa_render_samples = 16
                except AttributeError:
                    pass
            
            start_time = time.time()
            bpy.ops.render.render(write_still=False)
            duration = time.time() - start_time
            
            results.append({
                "area": r[4],
                "time": duration
            })
            
    finally:
        # Restore settings
        scene.render.use_border = original_settings["use_border"]
        scene.render.border_min_x = original_settings["border_min_x"]
        scene.render.border_max_x = original_settings["border_max_x"]
        scene.render.border_min_y = original_settings["border_min_y"]
        scene.render.border_max_y = original_settings["border_max_y"]
        scene.render.use_crop_to_border = original_settings["use_crop_to_border"]
        
        if scene.render.engine == 'CYCLES':
            scene.cycles.samples = original_settings["samples"]
        else:
            try:
                scene.eevee.taa_render_samples = original_settings["samples"]
            except AttributeError:
                pass
                
        if hasattr(scene.render, "use_persistent_data"):
            scene.render.use_persistent_data = original_settings["use_persistent_data"]

    # Write output
    with open(output_path, 'w') as f:
        json.dump(results, f)
        
    print(f"Benchmark worker finished successfully. Wrote to {output_path}")

if __name__ == "__main__":
    main()

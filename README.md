# Blender Scene Calibration

A production-quality Blender add-on designed to perform comprehensive render performance analysis for both static scenes and animations. The tool provides deep insights into scene complexity, identifies rendering bottlenecks, estimates VRAM usage, and predicts actual render times using a hardware-calibrated benchmark engine.

<img width="1352" height="952" alt="image" src="https://github.com/user-attachments/assets/d316c921-b262-49df-8d1b-739bddeff387" />


## Project Structure

```text
blender_scene_analyzer/
├── build_addon.py               # Deployment script to package the add-on
└── render_analyzer/             # Main add-on package
    ├── __init__.py              # Add-on registration and lifecycle management
    ├── analyzers/               # Deep-inspection modules for scene data
    │   ├── hardware_analyzer.py # System hardware profiling
    │   ├── lighting_analyzer.py # Light count, bounce, and shadow analysis
    │   ├── material_analyzer.py # Shader node complexity inspection
    │   ├── mesh_analyzer.py     # Depsgraph-evaluated polycount/modifier analysis
    │   ├── scene_analyzer.py    # General scene statistics
    │   ├── texture_analyzer.py  # Image resolution and memory analysis
    │   └── volume_analyzer.py   # Volumetric domain and scattering analysis
    ├── estimation/              # Mathematics and prediction engines
    │   ├── benchmark_engine.py  # Non-blocking render sampling controller
    │   ├── complexity_score.py  # Calculates Cycles/Eevee abstract scores
    │   ├── memory_estimator.py  # VRAM and System RAM calculations
    │   └── render_time_estimator.py # Intelligent scaling and benchmark extrapolation
    ├── operators/               # Interactive Blender operators (buttons/actions)
    │   ├── analyze_animation.py
    │   ├── analyze_scene.py
    │   ├── benchmark_render.py
    │   └── export_report.py
    ├── reporting/               # I/O handling
    │   └── export_json.py       # JSON report generation
    ├── ui/                      # Blender interface code
    │   ├── lists.py             # UIList templates for bottlenecks/textures
    │   ├── panels.py            # Sidebar panel definitions
    │   └── properties.py        # Scene property definitions and state storage
    └── utils/                   # Shared utilities
        ├── helpers.py           # Dependency graph and fingerprinting tools
        ├── scene_cache.py       # Cache management for instant UI redraws
        └── statistics.py        # Data classes for strict typing
```

## Features

- **Static Complexity Analysis:** Computes a theoretical complexity score for both Cycles and Eevee based on geometry, materials, textures, lighting, and volumetric data.
- **Hardware-Calibrated Benchmarking:** Runs a fast, non-blocking render benchmark (rendering 5 small 10%x10% border regions) to gauge actual hardware performance without freezing the Blender UI.
- **Render Time Estimation:** Combines static analysis and real-world benchmark timings to accurately predict single-frame and full-animation render times.
- **Memory Estimation:** Estimates VRAM consumption for geometry and textures, as well as total System RAM requirements.
- **Bottleneck Identification:** Scans the evaluated dependency graph to pinpoint the exact objects, modifiers, or massive textures causing performance hits.
- **Dashboard UI:** Clean, intuitive N-panel in the 3D viewport displaying real-time metrics and dynamic estimates.
- **Report Export:** Export comprehensive diagnostic reports to JSON for external analysis or production tracking.

## Installation

1. **Build the Add-on:**
   Run the provided build script to package the add-on into a deployable `.zip` file:
   ```bash
   python build_addon.py
   ```
   This will generate `render_analyzer_addon.zip` in the root directory.

2. **Install in Blender:**
   - Open Blender (supports 4.2 LTS, 4.3+, and 4.4+).
   - Navigate to `Edit` > `Preferences` > `Add-ons`.
   - Click **Install** and select the generated `render_analyzer_addon.zip`.
   - Check the box next to **Render Performance Analyzer** to enable it.

## Usage

Once installed, open the 3D Viewport and press `N` to open the sidebar. Navigate to the **Render Analyzer** tab.

1. **Analyze Scene:** Click this to perform an instant, static analysis of your current scene. This will populate the dashboard with complexity scores, memory estimates, and a theoretical time estimation.
2. **Run Render Benchmark:** Click this to run a live hardware test. The UI will remain responsive while the engine renders 5 small regions. Once complete, the estimation engine uses this real-world data to calibrate and display a highly accurate **Est. Frame Time (Benchmark)**.
3. **Analyze Animation:** After running the benchmark, use this tool to estimate the total duration required to render the active frame range.
4. **Top Bottlenecks:** Expand the bottleneck panel to see exactly which objects or textures are costing you the most memory or processing time.

## Compatibility
- Tested heavily against the new Blender 4.2 LTS API standards.
- Fully compatible with both Cycles and Eevee render pipelines.
- Safely handles complex setups including heavy Modifiers and Geometry Nodes by reading the evaluated dependency graph (`evaluated_depsgraph_get`).

## Example Output Json

{
    "fingerprint": "492d639f54610a461987181e9d28f5fbd686cba75130ad16de59d62e8fbdd43d",
    "snapshot": {
        "hardware": {
            "cpu_name": "Intel64 Family 6 Model 141 Stepping 1, GenuineIntel",
            "ram_gb": 7.7,
            "gpu_names": [
                "NVIDIA GeForce GTX 1650 with Max-Q Design",
                "NVIDIA GeForce GTX 1650 with Max-Q Design"
            ],
            "gpu_vendor": "NVIDIA",
            "cuda_enabled": false,
            "optix_enabled": false,
            "hip_enabled": false,
            "metal_enabled": false,
            "performance_tier": "Entry"
        },
        "scene_stats": {
            "total_objects": 52,
            "visible_objects": 52,
            "hidden_objects": 0,
            "meshes": 42,
            "lights": 3,
            "cameras": 4,
            "curves": 0,
            "volumes": 0,
            "materials": 23,
            "textures": 29,
            "instances": 0,
            "collections": 1,
            "geometry_node_objects": 0,
            "particle_systems": 0,
            "hair_systems": 0,
            "total_vertices": 345980,
            "total_edges": 809119,
            "total_faces": 463410,
            "total_triangles": 0,
            "bounds_min": [
                -2.9350996017456055,
                -5.702177047729492,
                -0.20000015199184418
            ],
            "bounds_max": [
                6.775911808013916,
                3.036269187927246,
                4.694690227508545
            ]
        },
        "cycles_score": {
            "mesh_score": 9.2682,
            "modifier_score": 0.0,
            "shader_score": 1.02,
            "lighting_score": 0.8999999999999999,
            "volume_score": 0.0,
            "render_settings_score": 16.3,
            "total_score": 27.4882,
            "category": "Light"
        },
        "eevee_score": {
            "mesh_score": 13.9023,
            "modifier_score": 0.0,
            "shader_score": 1.275,
            "lighting_score": 3.5999999999999996,
            "volume_score": 0.0,
            "render_settings_score": 16.299999999999997,
            "total_score": 35.077299999999994,
            "category": "Light"
        },
        "memory_estimate": {
            "geometry_vram_mb": 66.29133224487305,
            "texture_vram_mb": 0,
            "volume_vram_mb": 0.0,
            "total_vram_mb": 366.29133224487305,
            "total_system_ram_mb": 1463.5495986938477
        },
        "top_bottlenecks": [
            {
                "object_name": "i2stay0053",
                "impact_score": 20.0,
                "contribution_percent": 100.0,
                "primary_cause": "Moderate Poly Count (1.0x Amplification)"
            }
        ],
        "top_textures": [],
        "render_settings": {
            "engine": "CYCLES",
            "resolution_x": 3000,
            "resolution_y": 2257,
            "resolution_percentage": 100,
            "samples": 1096,
            "adaptive_sampling": true,
            "max_bounces": 12,
            "diffuse_bounces": 4,
            "glossy_bounces": 4,
            "transmission_bounces": 12,
            "caustics_reflective": true,
            "caustics_refractive": true,
            "denoising": true,
            "motion_blur": false,
            "depth_of_field": false,
            "render_settings_cost_score": 163
        },
        "instances": []
    }
}

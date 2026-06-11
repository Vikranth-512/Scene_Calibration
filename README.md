# Blender Scene Calibration

A production-quality Blender add-on designed to perform comprehensive render performance analysis for both static scenes and animations. The tool provides deep insights into scene complexity, identifies rendering bottlenecks, estimates VRAM usage, and predicts actual render times using a hardware-calibrated benchmark engine.

<img width="1236" height="897" alt="Screenshot 2026-06-11 114300" src="https://github.com/user-attachments/assets/4f8151ca-c734-4a8d-aaba-840c1d27522a" />

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

# Blender Scene Calibration

A production-quality Blender add-on for comprehensive render performance analysis and ML training-data collection. The tool provides deep insights into scene complexity, identifies rendering bottlenecks, estimates VRAM usage, predicts render times via hardware-calibrated benchmarks, and automatically scrapes structured feature vectors paired with ground-truth render timings for machine-learning research.

<img width="1352" height="952" alt="image" src="https://github.com/user-attachments/assets/d316c921-b262-49df-8d1b-739bddeff387" />

## Project Structure

```text
blender_scene_analyzer/
├── build_addon.py                # Deployment script to package the add-on
└── render_analyzer/              # Main add-on package
    ├── __init__.py               # Add-on registration and lifecycle management
    ├── analyzers/                # Deep-inspection modules for scene data
    │   ├── hardware_analyzer.py  # System hardware profiling
    │   ├── lighting_analyzer.py  # Light count, bounce, and shadow analysis
    │   ├── material_analyzer.py  # Shader node complexity inspection
    │   ├── mesh_analyzer.py      # Depsgraph-evaluated polycount/modifier analysis
    │   ├── scene_analyzer.py     # General scene statistics
    │   ├── texture_analyzer.py   # Image resolution and memory analysis
    │   └── volume_analyzer.py    # Volumetric domain and scattering analysis
    ├── estimation/               # Mathematics and prediction engines
    │   ├── benchmark_engine.py   # Non-blocking render sampling controller
    │   ├── complexity_score.py   # Calculates Cycles/Eevee abstract scores
    │   ├── memory_estimator.py   # VRAM and System RAM calculations
    │   └── render_time_estimator.py # Intelligent scaling and benchmark extrapolation
    ├── ml/                       # Machine-learning data pipeline
    │   ├── __init__.py
    │   ├── feature_schema.py     # Versioned feature definitions (FEATURES_V1)
    │   ├── schema_registry.py    # Schema version manager
    │   ├── feature_extractor.py  # Pure-function snapshot → feature-vector extraction
    │   ├── dataset_row.py        # DatasetRow dataclass with SHA-256 integrity hash
    │   ├── dataset_manager.py    # Dataset path management and validation
    │   ├── dataset_export.py     # JSONL append and single-row JSON export
    │   └── telemetry.py          # bpy render-handler hooks for automatic data capture
    ├── operators/                # Interactive Blender operators (buttons/actions)
    │   ├── analyze_animation.py
    │   ├── analyze_scene.py
    │   ├── benchmark_render.py
    │   └── export_report.py
    ├── reporting/                # I/O handling
    │   └── export_json.py        # JSON report generation
    ├── ui/                       # Blender interface code
    │   ├── lists.py              # UIList templates for bottlenecks/textures
    │   ├── panels.py             # Sidebar panel definitions
    │   └── properties.py         # Scene property definitions and state storage
    └── utils/                    # Shared utilities
        ├── helpers.py            # Dependency graph and fingerprinting tools
        ├── scene_cache.py        # Cache management for instant UI redraws
        └── statistics.py         # Data classes for strict typing
```

## Features

### Render Performance Analysis
- **Static Complexity Analysis** — Computes a theoretical complexity score for both Cycles and Eevee based on geometry, materials, textures, lighting, and volumetric data.
- **Hardware-Calibrated Benchmarking** — Runs a fast, non-blocking render benchmark (5 small 10×10 % border regions) to gauge actual hardware performance without freezing the UI.
- **Render Time Estimation** — Combines static analysis and real-world benchmark timings to predict single-frame and full-animation render times.
- **Memory Estimation** — Estimates VRAM consumption for geometry/textures and total System RAM requirements.
- **Bottleneck Identification** — Scans the evaluated dependency graph to pinpoint exact objects, modifiers, or textures causing performance hits.
- **Dashboard UI** — Clean, intuitive N-panel in the 3D viewport displaying real-time metrics and dynamic estimates.
- **Report Export** — Export comprehensive diagnostic reports to JSON for external analysis or production tracking.

### ML Data Collection
- **Automatic Telemetry** — Hooks into Blender's `render_init` / `render_complete` handlers to capture feature snapshots and ground-truth render times with zero manual effort.
- **Versioned Feature Schema** — All features are defined in a centralized, versioned schema (`feature_schema.py`) ensuring consistency across dataset versions and forward compatibility.
- **Structured JSONL Output** — Each render produces a `DatasetRow` containing the full feature vector, metadata, and target timings, appended to a schema-versioned JSONL file (`~/RenderAnalyzer/datasets/dataset_v{N}.jsonl`).
- **Integrity Hashing** — SHA-256 hashes over strictly-ordered feature vectors detect duplicates, corruption, and schema drift.
- **Validation Pipeline** — Schema-aware validation enforces key completeness, numeric finiteness, and semantic consistency (e.g., mutual exclusivity of compute backends) before any row is persisted.

## Feature Schema (v1)

The ML pipeline extracts a fixed-width, 55-dimensional feature vector per render. All values are `float` with a default of `0.0`.

| Group | Features |
|---|---|
| **Geometry** (11) | `total_evaluated_faces`, `total_vertices`, `mesh_count`, `largest_mesh_faces`, `mean_mesh_faces`, `median_mesh_faces`, `modifier_count`, `subdivision_count`, `geometry_nodes_count`, `instance_count`, `instance_face_equivalent` |
| **Materials** (7) | `material_count`, `glass_material_count`, `volume_material_count`, `displacement_material_count`, `total_shader_nodes`, `average_shader_nodes`, `max_shader_nodes` |
| **Textures** (5) | `texture_count`, `texture_memory_mb`, `vram_estimate_mb`, `largest_texture_pixels`, `mean_texture_pixels` |
| **Lighting** (7) | `light_count`, `sun_count`, `point_count`, `spot_count`, `area_count`, `emissive_material_count`, `hdri_count` |
| **Volumetrics** (4) | `volume_count`, `volume_world_space_m3`, `mean_volume_density`, `max_volume_density` |
| **Render Settings** (7) | `samples`, `max_bounces`, `resolution_x`, `resolution_y`, `resolution_pixels`, `engine_cycles`, `engine_eevee` |
| **Hardware Tiers** (6) | `tier_entry`, `tier_moderate`, `tier_high`, `tier_extreme`, `tier_unknown`, `tier_cpu_only` |
| **Hardware Details** (2) | `system_ram_gb`, `gpu_vram_gb` |
| **Compute Backend** (9) | `optix_enabled`, `cuda_enabled`, `metal_enabled`, `hip_enabled`, `backend_cpu`, `backend_cuda`, `backend_optix`, `backend_hip`, `backend_metal` |
| **Complexity Scores** (5) | `complexity_score`, `geometry_score`, `material_score`, `lighting_score`, `volume_score` |

**Target variable:** `actual_render_time_seconds` (captured automatically on render completion).

## Installation

1. **Build the Add-on:**
   ```bash
   python build_addon.py
   ```
   This generates `render_analyzer_addon.zip` in the project root.

2. **Install in Blender:**
   - Open Blender (4.2 LTS, 4.3+, 4.4+).
   - Navigate to `Edit` > `Preferences` > `Add-ons`.
   - Click **Install** and select `render_analyzer_addon.zip`.
   - Enable **Render Performance Analyzer**.

## Usage

Open the 3D Viewport, press `N` to reveal the sidebar, and navigate to the **Render Analyzer** tab.

1. **Analyze Scene** — Instant static analysis populating the dashboard with complexity scores, memory estimates, and theoretical time estimations.
2. **Run Render Benchmark** — Live hardware test rendering 5 small regions. The UI remains responsive; results calibrate the **Est. Frame Time (Benchmark)**.
3. **Analyze Animation** — Estimates total duration for the active frame range (requires a prior benchmark).
4. **Top Bottlenecks** — Expand the bottleneck panel to identify the most expensive objects and textures.
5. **Enable ML Telemetry** — Toggle in the panel to begin automatic dataset collection. Every subsequent render appends a validated row to the local JSONL dataset.

## Compatibility

- Tested against Blender 4.2 LTS API standards.
- Fully compatible with Cycles and Eevee render pipelines.
- Safely handles complex setups including heavy Modifiers and Geometry Nodes via the evaluated dependency graph (`evaluated_depsgraph_get`).

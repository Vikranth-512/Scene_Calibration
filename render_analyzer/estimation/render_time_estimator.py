import dataclasses
from typing import Protocol
from ..utils.statistics import SceneAnalysisSnapshot

@dataclasses.dataclass
class EstimationResult:
    estimated_frame_time_seconds: float = 0.0
    estimated_animation_time_seconds: float = 0.0
    confidence_score: float = 0.0

class BaseEstimator(Protocol):
    def estimate(self, scene_metrics: SceneAnalysisSnapshot, benchmark_data_json: str = None) -> EstimationResult:
        ...

class RuleBasedEstimator:
    def estimate(self, scene_metrics: SceneAnalysisSnapshot, benchmark_data_json: str = None) -> EstimationResult:
        result = EstimationResult()
        
        # Calculate static rule-based estimate first
        engine = scene_metrics.render_settings.engine
        score = scene_metrics.cycles_score.total_score if engine == 'CYCLES' else scene_metrics.eevee_score.total_score
        
        # Base assumption: a score of 100 takes 5 minutes per frame in Cycles at 128 samples
        static_base_time = (score / 100.0) * 300.0
        
        if engine == 'CYCLES':
            static_sample_ratio = scene_metrics.render_settings.samples / 128.0
            static_estimate = static_base_time * static_sample_ratio
        else:
            static_estimate = static_base_time * 0.1 # Eevee is much faster
            
        # M-01: Apply Hardware Performance Factor
        tier = scene_metrics.hardware.performance_tier
        hardware_factor = 1.8 # Default / Entry
        if tier == "Extreme": hardware_factor = 0.4
        elif tier == "High": hardware_factor = 0.7
        elif tier == "Moderate": hardware_factor = 1.0
        elif tier == "Low": hardware_factor = 1.4
        elif tier == "Entry": hardware_factor = 1.8
        
        static_estimate *= hardware_factor
            
        # If we have benchmark data, use it
        if benchmark_data_json:
            import json
            try:
                import numpy as np
                results = json.loads(benchmark_data_json)
                
                if not results or sum(r["time"] for r in results) <= 0:
                    raise ValueError("No valid benchmark samples.")
                
                res_x = scene_metrics.render_settings.resolution_x
                res_y = scene_metrics.render_settings.resolution_y
                res_pct = scene_metrics.render_settings.resolution_percentage / 100.0
                
                full_width = int(res_x * res_pct)
                full_height = int(res_y * res_pct)
                full_pixels = full_width * full_height
                
                pixels_arr = []
                times_arr = []
                
                for r in results:
                    sample_pixels = full_pixels * r["area"]
                    pixels_arr.append(sample_pixels)
                    times_arr.append(r["time"])
                
                # --- Tier 1: Linear regression (best case) ---
                m, c = np.polyfit(pixels_arr, times_arr, 1)
                pixel_cost = float(m)
                fixed_overhead = max(0.0, float(c))  # Clamp negative overhead to 0
                
                print("\n--- BENCHMARK ESTIMATION LOG ---")
                print(f"Sample Areas: {[r['area'] for r in results]}")
                print(f"Sample Times: {times_arr}")
                print(f"Regression slope (pixel_cost): {pixel_cost:.10f}")
                print(f"Regression intercept (overhead): {float(c):.4f} -> clamped: {fixed_overhead:.4f}")
                
                if pixel_cost > 0:
                    benchmark_estimate = fixed_overhead + (pixel_cost * full_pixels)
                    confidence = 0.90
                    print(f"Tier 1 (Regression): {benchmark_estimate:.2f} sec")
                else:
                    # --- Tier 2: Extrapolate from largest sample ---
                    # Regression slope is bad (noise), but the raw timings are real.
                    # Use the largest-area sample to scale linearly.
                    largest = max(results, key=lambda r: r["area"])
                    benchmark_estimate = largest["time"] / largest["area"]
                    confidence = 0.75
                    print(f"Tier 2 (Largest-sample extrapolation): {benchmark_estimate:.2f} sec")
                
                print(f"Static Estimate Reference: {static_estimate:.2f} sec")
                print(f"Confidence: {confidence}")
                print("--------------------------------\n")
                    
                # Sanity bounds — warn but don't reject
                if benchmark_estimate > static_estimate * 100:
                    print("WARNING: Benchmark estimate exceeds 100x static score.")
                if benchmark_estimate < static_estimate / 100:
                    print("WARNING: Benchmark estimate is less than 1/100x static score.")
                    
                result.estimated_frame_time_seconds = benchmark_estimate
                result.confidence_score = confidence
                
            except Exception as e:
                print(f"Benchmark estimation failed: {e}")
                print("Falling back to static hardware-calibrated estimate.")
                result.estimated_frame_time_seconds = static_estimate
                result.confidence_score = 0.40
        else:
            # Fallback to pure rule-based estimation
            result.estimated_frame_time_seconds = static_estimate
            result.confidence_score = 0.40
            
        return result


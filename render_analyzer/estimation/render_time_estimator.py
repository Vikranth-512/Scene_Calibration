import dataclasses
from typing import Protocol
from ..utils.statistics import SceneAnalysisSnapshot

@dataclasses.dataclass
class EstimationResult:
    estimated_frame_time_seconds: float = 0.0
    estimated_animation_time_seconds: float = 0.0
    confidence_score: float = 0.0

class BaseEstimator(Protocol):
    def estimate(self, scene_metrics: SceneAnalysisSnapshot, average_benchmark_time: float = None) -> EstimationResult:
        ...

class RuleBasedEstimator:
    def estimate(self, scene_metrics: SceneAnalysisSnapshot, average_benchmark_time: float = None) -> EstimationResult:
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
            
        # If we have benchmark data, use it as the base
        if average_benchmark_time and average_benchmark_time > 0:
            res_x = scene_metrics.render_settings.resolution_x
            res_y = scene_metrics.render_settings.resolution_y
            res_pct = scene_metrics.render_settings.resolution_percentage / 100.0
            
            full_width = int(res_x * res_pct)
            full_height = int(res_y * res_pct)
            full_pixels = full_width * full_height
            
            # The benchmark is hardcoded to 10% x 10% border regions
            border_width_pct = 0.1
            border_height_pct = 0.1
            border_area_pct = border_width_pct * border_height_pct # 0.01 (1%)
            
            sample_width = int(full_width * border_width_pct)
            sample_height = int(full_height * border_height_pct)
            sample_pixels = sample_width * sample_height
            
            time_per_pixel = average_benchmark_time / sample_pixels if sample_pixels > 0 else 0
            
            # Corrected Extrapolation logic: No extra multipliers!
            # time_per_pixel * full_pixels properly scales the area.
            benchmark_estimate = time_per_pixel * full_pixels
            
            # Logging the exact pipeline variables requested for debugging
            print("\n--- BENCHMARK ESTIMATION LOG ---")
            print(f"Sample Width: {sample_width}")
            print(f"Sample Height: {sample_height}")
            print(f"Sample Pixels: {sample_pixels}")
            print(f"Full Width: {full_width}")
            print(f"Full Height: {full_height}")
            print(f"Full Pixels: {full_pixels}")
            print(f"Sample Time: {average_benchmark_time:.4f} sec")
            print(f"Time Per Pixel: {time_per_pixel:.8f} sec")
            print(f"Area Ratio: {full_pixels / sample_pixels if sample_pixels > 0 else 0:.2f}")
            print(f"Estimated Full Frame: {benchmark_estimate:.2f} sec")
            print(f"Static Estimate Reference: {static_estimate:.2f} sec")
            print("--------------------------------\n")
            
            # Sanity Validation Layer
            # We add a 60-second fixed overhead buffer to the upper bound to prevent 
            # false positives on very lightweight scenes (like the default cube) where 
            # static_estimate is nearly zero but engine init overhead is non-zero.
            upper_bound = (static_estimate * 100) + 60.0
            lower_bound = (static_estimate / 100)
            
            if benchmark_estimate > upper_bound or benchmark_estimate < lower_bound:
                print("WARNING: Benchmark estimate appears invalid. Possible scaling/extrapolation error detected.")
                print("Falling back to static estimate.")
                result.estimated_frame_time_seconds = static_estimate
                result.confidence_score = 0.4
            else:
                result.estimated_frame_time_seconds = benchmark_estimate
                result.confidence_score = 0.85
        else:
            # Fallback to pure rule-based estimation
            result.estimated_frame_time_seconds = static_estimate
            result.confidence_score = 0.4
            
        return result

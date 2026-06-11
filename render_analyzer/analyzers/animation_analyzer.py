import bpy

def get_animation_range():
    scene = bpy.context.scene
    return scene.frame_start, scene.frame_end

# Animation analysis is largely handled by the modal operator which samples frames
# and aggregates the standard SceneAnalysisSnapshot for those frames.

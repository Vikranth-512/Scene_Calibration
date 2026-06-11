import platform
import ctypes
import bpy
from ..utils.statistics import HardwareProfile

def get_total_ram_gb() -> float:
    if platform.system() == "Windows":
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        try:
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            return round(stat.ullTotalPhys / (1024 ** 3), 1)
        except Exception:
            return 0.0
    elif platform.system() == "Linux":
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemTotal' in line:
                        kb = int(line.split()[1])
                        return round(kb / (1024 ** 2), 1)
        except Exception:
            return 0.0
    elif platform.system() == "Darwin":
        import subprocess
        try:
            out = subprocess.check_output(['sysctl', '-n', 'hw.memsize'])
            return round(int(out.strip()) / (1024 ** 3), 1)
        except Exception:
            return 0.0
    return 0.0

def analyze_hardware() -> HardwareProfile:
    profile = HardwareProfile()
    profile.cpu_name = platform.processor() or "Unknown CPU"
    profile.ram_gb = get_total_ram_gb()
    
    # Try to get Cycles devices
    try:
        cycles_prefs = bpy.context.preferences.addons.get('cycles')
        if cycles_prefs:
            cprefs = cycles_prefs.preferences
            # Initialize devices if not done
            cprefs.get_devices()
            
            # Active API
            device_type = cprefs.compute_device_type
            if device_type == 'CUDA':
                profile.cuda_enabled = True
            elif device_type == 'OPTIX':
                profile.optix_enabled = True
            elif device_type == 'HIP':
                profile.hip_enabled = True
            elif device_type == 'METAL':
                profile.metal_enabled = True
                
            # Collect GPU names
            gpus = []
            for device in cprefs.devices:
                if device.type != 'CPU' and device.use:
                    gpus.append(device.name)
            
            if not gpus:
                # If no active GPUs, just list all available
                for device in cprefs.devices:
                    if device.type != 'CPU':
                        gpus.append(device.name)
            
            profile.gpu_names = gpus
            if gpus:
                name_lower = gpus[0].lower()
                if "nvidia" in name_lower or "rtx" in name_lower or "gtx" in name_lower:
                    profile.gpu_vendor = "NVIDIA"
                elif "amd" in name_lower or "radeon" in name_lower:
                    profile.gpu_vendor = "AMD"
                elif "apple" in name_lower or "m1" in name_lower or "m2" in name_lower or "m3" in name_lower:
                    profile.gpu_vendor = "Apple"
                elif "intel" in name_lower or "arc" in name_lower:
                    profile.gpu_vendor = "Intel"
                    
                # Very rough performance tier
                if "4090" in name_lower or "4080" in name_lower or "7900" in name_lower:
                    profile.performance_tier = "Extreme"
                elif "3090" in name_lower or "3080" in name_lower or "4070" in name_lower or "m3 max" in name_lower:
                    profile.performance_tier = "High"
                elif "3060" in name_lower or "4060" in name_lower or "2080" in name_lower:
                    profile.performance_tier = "Moderate"
                else:
                    profile.performance_tier = "Entry"
            else:
                profile.gpu_vendor = "None"
                profile.performance_tier = "CPU Only"
    except Exception as e:
        print(f"Error accessing hardware info: {e}")
        
    return profile

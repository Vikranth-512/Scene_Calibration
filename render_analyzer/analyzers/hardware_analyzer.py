import platform
import ctypes
import bpy
import subprocess
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
        try:
            out = subprocess.check_output(['sysctl', '-n', 'hw.memsize'])
            return round(int(out.strip()) / (1024 ** 3), 1)
        except Exception:
            return 0.0
    return 0.0

def get_gpu_vram_gb() -> float:
    vram_mb = -1.0
    
    # 1. nvidia-smi
    try:
        out = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'], text=True, stderr=subprocess.DEVNULL)
        vram = sum(int(x.strip()) for x in out.strip().split('\n') if x.strip().isdigit())
        if vram > 0:
            return round(vram / 1024.0, 2)
    except Exception:
        pass
        
    # 2. PowerShell / CIM
    if platform.system() == "Windows":
        try:
            out = subprocess.check_output(['powershell', '-Command', 'Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty AdapterRAM'], text=True, stderr=subprocess.DEVNULL)
            rams = [int(line.strip()) for line in out.splitlines() if line.strip().isdigit()]
            if rams:
                return round(max(rams) / (1024**3), 2)
        except Exception:
            pass
            
    # 3. macOS fallback
    if platform.system() == "Darwin":
        try:
            out = subprocess.check_output(['system_profiler', 'SPDisplaysDataType'], text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                if 'VRAM' in line or 'Memory' in line:
                    parts = line.strip().split()
                    for i, p in enumerate(parts):
                        if p in {'MB', 'GB'} and i > 0:
                            val = float(parts[i-1])
                            if p == 'MB': val /= 1024.0
                            return round(val, 2)
        except Exception:
            pass
            
    return -1.0

def analyze_hardware(scene=None) -> HardwareProfile:
    if scene is None:
        scene = bpy.context.scene
        
    profile = HardwareProfile()
    profile.cpu_name = platform.processor() or "Unknown CPU"
    profile.ram_gb = get_total_ram_gb()
    profile.gpu_vram_gb = get_gpu_vram_gb()
    
    # Try to get Cycles devices
    try:
        cycles_prefs = bpy.context.preferences.addons.get('cycles')
        if cycles_prefs:
            cprefs = cycles_prefs.preferences
            
            # Initialize/Refresh devices
            if hasattr(cprefs, 'refresh_devices'):
                cprefs.refresh_devices()
            elif hasattr(cprefs, 'get_devices'):
                cprefs.get_devices()
                
            # Hardware Availability
            for device in cprefs.devices:
                if device.type == 'CUDA':
                    profile.cuda_enabled = True
                elif device.type == 'OPTIX':
                    profile.optix_enabled = True
                elif device.type == 'HIP':
                    profile.hip_enabled = True
                elif device.type == 'METAL':
                    profile.metal_enabled = True
                    
            # Active Compute Backend
            if getattr(scene.cycles, 'device', 'CPU') == 'CPU':
                profile.active_compute_backend = "CPU"
            else:
                dt = str(getattr(cprefs, 'compute_device_type', 'NONE')).upper()
                if 'CUDA' in dt or dt == '1': profile.active_compute_backend = "CUDA"
                elif 'OPTIX' in dt or dt == '2': profile.active_compute_backend = "OPTIX"
                elif 'HIP' in dt or dt == '4': profile.active_compute_backend = "HIP"
                elif 'METAL' in dt or dt == '5': profile.active_compute_backend = "METAL"
                else: profile.active_compute_backend = "NONE"
                
            # Collect GPU names
            gpus = []
            for device in cprefs.devices:
                if device.type != 'CPU' and device.use:
                    gpus.append(device.name)
            
            if not gpus:
                # If no active GPUs, list available ones
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

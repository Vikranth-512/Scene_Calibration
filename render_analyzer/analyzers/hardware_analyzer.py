import platform
import ctypes
import re
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
    # 1. nvidia-smi (most accurate for NVIDIA)
    try:
        out = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'],
            text=True, stderr=subprocess.DEVNULL
        )
        vram = sum(int(x.strip()) for x in out.strip().split('\n') if x.strip().isdigit())
        if vram > 0:
            return round(vram / 1024.0, 2)
    except Exception:
        pass
        
    # 2. PowerShell CIM (future-proof Windows fallback)
    if platform.system() == "Windows":
        try:
            out = subprocess.check_output(
                ['powershell', '-Command',
                 'Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty AdapterRAM'],
                text=True, stderr=subprocess.DEVNULL
            )
            rams = [int(line.strip()) for line in out.splitlines() if line.strip().isdigit()]
            if rams:
                return round(max(rams) / (1024**3), 2)
        except Exception:
            pass
            
    # 3. macOS fallback
    if platform.system() == "Darwin":
        try:
            out = subprocess.check_output(
                ['system_profiler', 'SPDisplaysDataType'],
                text=True, stderr=subprocess.DEVNULL
            )
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


def parse_gpu_vendor(gpu_name: str) -> str:
    """Classify GPU vendor from device name string."""
    name_lower = gpu_name.lower()
    if "nvidia" in name_lower or "rtx" in name_lower or "gtx" in name_lower or "geforce" in name_lower or "quadro" in name_lower or "tesla" in name_lower:
        return "NVIDIA"
    elif "amd" in name_lower or "radeon" in name_lower or "rx " in name_lower:
        return "AMD"
    elif "intel" in name_lower or "arc " in name_lower:
        return "Intel"
    elif "apple" in name_lower or "m1" in name_lower or "m2" in name_lower or "m3" in name_lower or "m4" in name_lower:
        return "Apple"
    return "Unknown"


def parse_gpu_family(gpu_name: str) -> str:
    """Classify GPU into product family."""
    name_lower = gpu_name.lower()
    
    # NVIDIA families
    if "rtx" in name_lower:
        return "RTX"
    if "gtx" in name_lower:
        return "GTX"
    if "quadro" in name_lower:
        return "Quadro"
    if "tesla" in name_lower:
        return "Tesla"
    
    # AMD families
    if "rx " in name_lower or "rx-" in name_lower:
        return "RX"
    
    # Intel
    if "arc " in name_lower or "arc-" in name_lower:
        return "Arc"
    
    # Apple / Integrated
    if "apple" in name_lower or name_lower.startswith("m1") or name_lower.startswith("m2") or name_lower.startswith("m3") or name_lower.startswith("m4"):
        return "Integrated"
    
    # Intel integrated
    if "intel" in name_lower and ("hd" in name_lower or "uhd" in name_lower or "iris" in name_lower):
        return "Integrated"
    
    return "Unknown"


def parse_gpu_model_number(gpu_name: str) -> float:
    """Extract the primary numeric model identifier from a GPU name.
    
    Examples:
        GTX 1650 -> 1650
        RTX 3060 -> 3060
        RX 7900 -> 7900
        Quadro RTX 5000 -> 5000
    """
    # Match patterns like "GTX 1650", "RTX 3060 Ti", "RX 7900 XTX"
    match = re.search(r'(?:GTX|RTX|RX|Arc)\s*[A-Za-z]*\s*(\d{3,5})', gpu_name, re.IGNORECASE)
    if match:
        return float(match.group(1))
    
    # Fallback: find the largest 3-5 digit number in the name
    numbers = re.findall(r'\b(\d{3,5})\b', gpu_name)
    if numbers:
        return float(max(numbers, key=lambda x: int(x)))
    
    return -1.0


def parse_gpu_generation(gpu_name: str, model_number: float) -> float:
    """Determine GPU generation from model number and family.
    
    NVIDIA convention:
        GTX 10xx -> 10, GTX 16xx -> 16
        RTX 20xx -> 20, RTX 30xx -> 30, RTX 40xx -> 40, RTX 50xx -> 50
    
    AMD convention:
        RX 5xxx -> 5, RX 6xxx -> 6, RX 7xxx -> 7
    """
    if model_number < 0:
        return -1.0
    
    name_lower = gpu_name.lower()
    model_int = int(model_number)
    
    # NVIDIA
    if "nvidia" in name_lower or "geforce" in name_lower or "gtx" in name_lower or "rtx" in name_lower:
        if model_int >= 1000:
            # 1080 -> gen 10, 1650 -> gen 16, 2080 -> gen 20, etc.
            return float(model_int // 100)
        return -1.0
    
    # AMD
    if "amd" in name_lower or "radeon" in name_lower or "rx" in name_lower:
        if model_int >= 1000:
            return float(model_int // 1000)
        return -1.0
    
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
            
            # === 1. Hardware Capabilities ===
            for device in cprefs.devices:
                if device.type == 'CUDA':
                    profile.capability_cuda = True
                elif device.type == 'OPTIX':
                    profile.capability_optix = True
                elif device.type == 'HIP':
                    profile.capability_hip = True
                elif device.type == 'METAL':
                    profile.capability_metal = True
                    
            # === 2. Active Cycles Backend ===
            dt = str(getattr(cprefs, 'compute_device_type', 'NONE')).upper()
            if 'OPTIX' in dt:
                profile.active_compute_backend = "OPTIX"
            elif 'CUDA' in dt:
                profile.active_compute_backend = "CUDA"
            elif 'HIP' in dt:
                profile.active_compute_backend = "HIP"
            elif 'METAL' in dt:
                profile.active_compute_backend = "METAL"
            else:
                profile.active_compute_backend = "CPU"
            
            # === 3. Actual Render Device ===
            cycles_device = getattr(scene.cycles, 'device', 'CPU')
            profile.render_device = "GPU" if cycles_device == 'GPU' else "CPU"
                
            # === 4. GPU Names & Identity ===
            gpus = []
            for device in cprefs.devices:
                if device.type != 'CPU' and device.use:
                    gpus.append(device.name)
            
            if not gpus:
                for device in cprefs.devices:
                    if device.type != 'CPU':
                        gpus.append(device.name)
            
            profile.gpu_names = gpus
            if gpus:
                primary_gpu = gpus[0]
                
                # Vendor
                profile.gpu_vendor = parse_gpu_vendor(primary_gpu)
                
                # Family
                profile.gpu_family = parse_gpu_family(primary_gpu)
                
                # Model Number
                profile.gpu_model_number = parse_gpu_model_number(primary_gpu)
                
                # Generation
                profile.gpu_generation = parse_gpu_generation(primary_gpu, profile.gpu_model_number)
                    
                # Performance tier
                name_lower = primary_gpu.lower()
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

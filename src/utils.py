import subprocess
import threading
import time
import os

def startComfyui(startup_script_path):
    def run_comfyui():
        try:
            # Start ComfyUI with proper Python path
            env = os.environ.copy()
            env["PYTHONPATH"] = "/opt/ComfyUI"
            subprocess.run(
                ["python3", startup_script_path],
                env=env,
                check=True
            )
        except Exception as e:
            print(f"Error starting ComfyUI: {e}")
    
    # Start ComfyUI in a separate thread
    comfy_thread = threading.Thread(target=run_comfyui, daemon=True)
    comfy_thread.start()
    
    # Wait for ComfyUI to initialize
    time.sleep(5)
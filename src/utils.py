import subprocess
import os
import logging

def startComfyui(host, port):
    """
    Launch ComfyUI using init.sh script with specific environment variables
    
    Args:
        host (str): Host address for ComfyUI
        port (int): Port for ComfyUI
    """
    try:
        # Set environment variables
        env = os.environ.copy()
        env.update({
            "DIRECT_ADDRESS": host,
            "COMFYUI_PORT_HOST": str(port),
            "WEB_ENABLE_AUTH": "false",
            "CF_QUICK_TUNNELS": "false"
        })
        
        # Launch ComfyUI process using init.sh
        process = subprocess.Popen(
            ["init.sh"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        logging.info(f"Started ComfyUI on {host}:{port}")
        return process
        
    except Exception as e:
        logging.error(f"Failed to start ComfyUI: {e}")
        raise
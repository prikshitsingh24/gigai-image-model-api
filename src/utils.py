import os
import logging
import asyncio

async def startComfyui(host: str, port: int):
    """
    Launch ComfyUI using init.sh script with specific environment variables.
    
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
        process = await asyncio.create_subprocess_exec(
            "init.sh",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        logging.info(f"Started ComfyUI on {host}:{port} with  {process}")
        return process
        
    except Exception as e:
        logging.error(f"Failed to start ComfyUI: {e}")
        raise

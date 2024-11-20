import os
import logging
import subprocess

async def startComfyui(host: str, port: int):
        """
        Launch ComfyUI synchronously using init.sh script with specific environment variables.
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
            
            # Log before starting ComfyUI process
            logging.info(f"Starting ComfyUI on {host}:{port}...")

            # Launch ComfyUI process using init.sh (synchronously)
            process = subprocess.Popen(
                ["init.sh"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )

            # Log process ID
            logging.info(f"ComfyUI started with PID {process.pid}")
            return process

        except Exception as e:
            logging.error(f"Failed to start ComfyUI: {e}")
            raise

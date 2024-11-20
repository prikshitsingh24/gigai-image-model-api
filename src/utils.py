import os
import logging
import asyncio
import subprocess
from typing import Optional


async def execute(command: str, args: list, env_additions: Optional[dict] = None) -> Optional[int]:
    """
    Execute a command with specified arguments and environment variables.
    
    Args:
        command (str): The command to run.
        args (list): List of arguments for the command.
        env_additions (dict, optional): Additional environment variables to merge with the existing environment.
    
    Returns:
        int: The exit code of the process, or None if the process was terminated by a signal.
    """
    if env_additions is None:
        env_additions = {}

    # Merge parent environment with the additional environment variables
    env = os.environ.copy()
    env.update(env_additions)
    
    try:
        # Start the process asynchronously
        process = await asyncio.create_subprocess_exec(
            command, *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )

        # Handle the output asynchronously
        stdout, stderr = await process.communicate()

        # Log stdout and stderr
        if stdout:
            logging.info(stdout.decode())
        if stderr:
            logging.error(stderr.decode())

        # Log process exit
        exit_code = await process.wait()
        if exit_code == 0:
            logging.info(f"Process '{command}' exited successfully.")
        else:
            logging.error(f"Process '{command}' exited with code {exit_code}.")
        
        return exit_code

    except Exception as e:
        logging.error(f"Failed to execute process: {e}")
        return None


async def startComfyui(host: str, port: int):
    logging.info(f"Starting ComfyUI on {host}:{port}")
    """
    Start ComfyUI using the init.sh script with environment variables.
    
    Args:
        host (str): Host address for ComfyUI.
        port (int): Port for ComfyUI.
    """
    try:
        # Set environment variables
        env_additions = {
            "DIRECT_ADDRESS": host,
            "COMFYUI_PORT_HOST": str(port),
            "WEB_ENABLE_AUTH": "false",
            "CF_QUICK_TUNNELS": "false"
        }

        # Execute the init.sh script to start ComfyUI
        exit_code = await execute("init.sh", [], env_additions)

        if exit_code == 0:
            logging.info(f"ComfyUI started successfully on {host}:{port}")
        else:
            logging.error(f"ComfyUI failed to start with exit code {exit_code}")

    except Exception as e:
        logging.error(f"Error starting ComfyUI: {e}")



  

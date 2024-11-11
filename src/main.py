from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from typing import Dict
from enum import Enum
import aiofiles
import logging
import subprocess
import psutil
import time
import signal

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model type enum - updated to match ComfyUI's directory structure
class ModelType(str, Enum):
    checkpoints = "checkpoints"
    clip = "clip"
    clip_vision = "clip_vision"
    configs = "configs"
    controlnet = "controlnet"
    diffusers = "diffusers"
    diffusion_models = "diffusion_models"
    embeddings = "embeddings"
    gligen = "gligen"
    hypernetworks = "hypernetworks"
    loras = "loras"
    photomaker = "photomaker"
    style_models = "style_models"
    unet = "unet"
    upscale_models = "upscale_models"
    vae = "vae"
    vae_approx = "vae_approx"

# Base directory for models
MODEL_BASE_DIR = "/opt/ComfyUI/models"

# Ensure directories exist
for model_type in ModelType:
    os.makedirs(os.path.join(MODEL_BASE_DIR, model_type), exist_ok=True)


def restart_comfyui():
    try:
        # Start the container restart in the background
        print("Restarting container...")
        restart_process = subprocess.Popen(["docker", "restart", "gigai-image-model-runner"])
        
        # Start showing logs in real-time
        print("Following container logs...")
        logs_process = subprocess.Popen(["docker", "logs", "-f", "gigai-image-model-runner"])
        
        # Wait for the restart process to complete
        restart_process.wait()
        
        # Optionally, wait for the logs process to finish (this will run indefinitely until the logs are stopped)
        logs_process.wait()
    
    except subprocess.CalledProcessError as e:
        print(f"Error during container restart or log fetching: {e}")

@app.post("/upload/model/{model_type}")
async def upload_model(
    model_type: ModelType,
    model_file: UploadFile = File(...),
):
    try:
        # Validate file extension
        valid_extensions = {".safetensors", ".ckpt", ".pt", ".bin", ".sft", ".yaml"}
        file_ext = os.path.splitext(model_file.filename)[1].lower()
        if file_ext not in valid_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file extension. Allowed: {valid_extensions}"
            )

        # Create save path
        save_path = os.path.join(MODEL_BASE_DIR, model_type, model_file.filename)
        
        # Save file in chunks to handle large files
        async with aiofiles.open(save_path, 'wb') as out_file:
            while content := await model_file.read(1024 * 1024):  # 1MB chunks
                await out_file.write(content)

        # Set proper permissions
        os.chmod(save_path, 0o755)
        
        # Force refresh of model list
        try:
            os.utime(os.path.join(MODEL_BASE_DIR, model_type), None)
        except Exception:
            pass
        
        print({"status": "success","message": f"Model uploaded successfully to {model_type}","filename": model_file.filename})
        restart_comfyui()
        
    except Exception as e:
        logging.error(f"Error uploading model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/list")
async def list_models():
    models = {}
    for model_type in ModelType:
        model_dir = os.path.join(MODEL_BASE_DIR, model_type)
        if os.path.exists(model_dir):
            # Filter out placeholder files and get only actual model files
            files = [f for f in os.listdir(model_dir) 
                    if os.path.isfile(os.path.join(model_dir, f)) and 
                    not f.startswith("put_") and 
                    not f.endswith("_here")]
            models[model_type] = files
    return models

@app.delete("/models/{model_type}/{filename}")
async def delete_model(model_type: ModelType, filename: str):
    try:
        file_path = os.path.join(MODEL_BASE_DIR, model_type, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Model not found")
        
        os.remove(file_path)
        return {"status": "success", "message": f"Deleted {filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add a debug endpoint to check directory structure
@app.get("/debug/dirs")
async def debug_dirs():
    result = {}
    for model_type in ModelType:
        dir_path = os.path.join(MODEL_BASE_DIR, model_type)
        try:
            files = os.listdir(dir_path)
            result[model_type] = {
                "exists": os.path.exists(dir_path),
                "is_dir": os.path.isdir(dir_path),
                "permissions": oct(os.stat(dir_path).st_mode)[-3:],
                "files": files,
                "files_details": [
                    {
                        "name": f,
                        "is_file": os.path.isfile(os.path.join(dir_path, f)),
                        "size": os.path.getsize(os.path.join(dir_path, f))
                    } for f in files
                ]
            }
        except Exception as e:
            result[model_type] = {"error": str(e)}
    return result

def start():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start()

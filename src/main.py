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

from utils import startComfyui

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
STARTUP_SCRIPT_PATH = "/opt/ComfyUI/main.py"
MODEL_BASE_DIR = "/opt/ComfyUI/models"
WORKFLOW_BASE_DIR = "/opt/ComfyUI/workflows"

# Ensure directories exist
for model_type in ModelType:
    os.makedirs(os.path.join(MODEL_BASE_DIR, model_type), exist_ok=True)



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

          # Prepare response
        response = {
            "status": "success",
            "message": f"Model uploaded successfully to {model_type}. Server will restart.",
            "filename": model_file.filename,
            "requiresRestart": True  # Flag for frontend to know server will restart
        }
        
        # Start restart process in background without waiting
        subprocess.Popen(
            ["docker", "restart", "gigai-image-model-runner"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        return response
        
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

@app.get("/workflows/list")
async def list_workflows():
    workflows = {}
    
    # Walk through all directories and subdirectories inside WORKFLOW_BASE_DIR
    for root, dirs, files in os.walk(WORKFLOW_BASE_DIR):
        print(f"Checking directory: {root}")  # Debugging line
        print(f"Files found: {files}")        # Debugging line

        # Filter for .ts files only
        ts_files = [f for f in files if f.endswith(".ts")]
        
        if ts_files:
            # Get the relative path for the directory
            relative_dir = os.path.relpath(root, WORKFLOW_BASE_DIR)
            print(f"Relative directory: {relative_dir}")  # Debugging line
            
            if relative_dir == ".":
                relative_dir = "root"
            
            workflows[relative_dir] = ts_files
    
    print(f"Workflows found: {workflows}")  # Debugging line
    return workflows

def start():
    startComfyui(STARTUP_SCRIPT_PATH)
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import uvicorn
import os
from typing import Dict
from enum import Enum
import aiofiles
import logging

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model type enum
class ModelType(str, Enum):
    checkpoint = "checkpoints"
    lora = "loras"
    controlnet = "controlnet"
    embedding = "embeddings"
    vae = "vae"

# Base directory for models
MODEL_BASE_DIR = "/opt/ComfyUI/models"

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
        valid_extensions = {".safetensors", ".ckpt", ".pt", ".bin",".sft"}
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
        
        # Force refresh of model list (optional)
        try:
            os.utime(os.path.join(MODEL_BASE_DIR, model_type), None)
        except Exception:
            pass

        return {
            "status": "success",
            "message": f"Model uploaded successfully to {model_type}",
            "filename": model_file.filename,
            "path": save_path
        }
    except Exception as e:
        logging.error(f"Error uploading model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/list")
async def list_models():
    models = {}
    for model_type in ModelType:
        model_dir = os.path.join(MODEL_BASE_DIR, model_type)
        if os.path.exists(model_dir):
            models[model_type] = [f for f in os.listdir(model_dir) 
                                if os.path.isfile(os.path.join(model_dir, f))]
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
    
    
def start():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import boto3
from typing import Optional
import io
from PIL import Image

app = FastAPI(
    title="Face Verification API",
    description="Compare faces using AWS Rekognition",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "AWS Rekognition Face Verification API",
        "version": "1.0.0",
        "endpoints": {
            "verify": "/verify-faces",
            "health": "/health",
            "info": "/info",
            "docs": "/docs"
        },
        "usage": {
            "method": "POST",
            "endpoint": "/verify-faces",
            "content_type": "multipart/form-data",
            "required_fields": ["image1", "image2"],
            "optional_fields": ["similarity_threshold"]
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "face-verification", "version": "1.0.0"}

@app.get("/info")
async def service_info():
    """Service information"""
    return {
        "service": "AWS Rekognition Face Verification",
        "supported_formats": ["JPEG", "PNG"],
        "max_file_size": "5MB",
        "similarity_threshold_range": "0-100",
        "endpoints": {
            "verify": "/verify-faces",
            "health": "/health",
            "docs": "/docs"
        }
    }

# Usage:
# pip install fastapi boto3 pillow
# uvicorn app:app --host 0.0.0.0 --port 8000
# 
# Or for development with auto-reload:
# uvicorn app:app --reload --host 0.0.0.0 --port 8000
# 
# Then visit:
# http://localhost:8000 - API root
# http://localhost:8000/docs - API documentation

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

class FaceVerificationService:
    def __init__(self, region='us-east-1'):
        self.rekognition = boto3.client('rekognition', region_name=region)
        self.max_file_size = 20 * 1024 * 1024  # 20MB limit
        self.allowed_formats = {'image/jpeg', 'image/jpg', 'image/png'}
    
    def validate_image(self, file: UploadFile) -> bool:
        """Validate uploaded image file"""
        if file.content_type not in self.allowed_formats:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file format. Allowed: {', '.join(self.allowed_formats)}"
            )
        return True
    
    async def verify_faces(self, image1: UploadFile, image2: UploadFile, 
                          similarity_threshold: float = 80.0) -> dict:
        """Compare faces in two uploaded images"""
        try:
            # Validate files
            self.validate_image(image1)
            self.validate_image(image2)
            
            # Read file contents
            image1_bytes = await image1.read()
            image2_bytes = await image2.read()
            
            # Check file sizes
            if len(image1_bytes) > self.max_file_size or len(image2_bytes) > self.max_file_size:
                raise HTTPException(
                    status_code=413, 
                    detail="File too large. Maximum size is 5MB per image."
                )
            
            # Verify images can be opened
            try:
                Image.open(io.BytesIO(image1_bytes))
                Image.open(io.BytesIO(image2_bytes))
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid image format or corrupted file")
            
            # Call AWS Rekognition
            response = self.rekognition.compare_faces(
                SourceImage={'Bytes': image1_bytes},
                TargetImage={'Bytes': image2_bytes},
                SimilarityThreshold=similarity_threshold,
                QualityFilter='AUTO'
            )
            
            # Process response
            if response['FaceMatches']:
                match = response['FaceMatches'][0]
                return {
                    'verified': True,
                    'similarity': round(match['Similarity'], 2),
                    'confidence': round(match['Face']['Confidence'], 2),
                    'source_confidence': round(response.get('SourceImageFace', {}).get('Confidence', 0), 2),
                    'threshold_used': similarity_threshold,
                    'face_details': {
                        'bounding_box': match['Face']['BoundingBox'],
                        'age_range': match['Face'].get('AgeRange'),
                        'gender': match['Face'].get('Gender'),
                        'pose': match['Face'].get('Pose')
                    }
                }
            else:
                return {
                    'verified': False,
                    'similarity': 0.0,
                    'message': 'No matching faces found above threshold',
                    'threshold_used': similarity_threshold,
                    'unmatched_faces_count': len(response.get('UnmatchedFaces', []))
                }
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Face verification failed: {str(e)}")

# Initialize service
face_service = FaceVerificationService()

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

@app.post("/verify-faces")
async def verify_faces(
    image1: UploadFile = File(..., description="First image for comparison"),
    image2: UploadFile = File(..., description="Second image for comparison"),
    similarity_threshold: Optional[float] = Form(80.0, description="Similarity threshold (0-100)")
):
    """
    Compare faces in two uploaded images
    
    - **image1**: First image file (JPEG/PNG, max 5MB)
    - **image2**: Second image file (JPEG/PNG, max 5MB)
    - **similarity_threshold**: Minimum similarity score (0-100, default: 80)
    """
    if not 0 <= similarity_threshold <= 100:
        raise HTTPException(status_code=400, detail="Similarity threshold must be between 0 and 100")
    
    result = await face_service.verify_faces(image1, image2, similarity_threshold)
    return JSONResponse(content=result)

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
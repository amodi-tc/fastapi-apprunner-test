# OEPE Image Verification

A FastAPI-based service that uses AWS Rekognition to compare faces in uploaded images.

## Features

- Face comparison using AWS Rekognition
- RESTful API with automatic documentation
- Support for JPEG and PNG images
- Configurable similarity threshold
- Health check endpoints
- CORS enabled for web applications

## Local Development

### Prerequisites

- Python 3.13+
- Poetry
- AWS credentials configured

### Setup

1. Install dependencies:
```bash
poetry install
```

2. Run the application:
```bash
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. Access the API:
- API Root: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Docker Deployment

### Local Docker Build

```bash
# Build the Docker image
docker build -t oepe-image-verification .

# Run the container
docker run -p 8000:8000 oepe-image-verification
```

### AWS App Runner Deployment

#### Prerequisites

1. AWS CLI configured with appropriate permissions
2. Docker installed locally
3. AWS ECR repository created

#### Deployment Steps

1. **Create ECR Repository** (if not exists):
```bash
aws ecr create-repository --repository-name oepe-image-verification
```

2. **Get ECR login token**:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

3. **Build and tag the image**:
```bash
docker build -t oepe-image-verification .
docker tag oepe-image-verification:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/oepe-image-verification:latest
```

4. **Push to ECR**:
```bash
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/oepe-image-verification:latest
```

5. **Deploy to App Runner**:

   a. Go to AWS App Runner console
   b. Click "Create service"
   c. Choose "Container registry"
   d. Select "Amazon ECR" and choose your repository
   e. Configure service settings:
      - Service name: `oepe-image-verification`
      - Port: `8000`
      - CPU: `1 vCPU`
      - Memory: `2 GB`
   f. Configure environment variables (if needed):
      - `AWS_DEFAULT_REGION`: `us-east-1`
   g. Set up IAM role with Rekognition permissions
   h. Configure auto-scaling (optional)
   i. Click "Create & deploy"

#### Required IAM Permissions

Create an IAM role with the following policy for App Runner:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "rekognition:CompareFaces"
            ],
            "Resource": "*"
        }
    ]
}
```

## API Usage

### Verify Faces

**Endpoint**: `POST /verify-faces`

**Content-Type**: `multipart/form-data`

**Parameters**:
- `image1`: First image file (JPEG/PNG, max 20MB)
- `image2`: Second image file (JPEG/PNG, max 20MB)
- `similarity_threshold`: Minimum similarity score (0-100, default: 80)

**Example Response**:
```json
{
    "verified": true,
    "similarity": 95.2,
    "confidence": 99.8,
    "source_confidence": 99.9,
    "threshold_used": 80.0,
    "face_details": {
        "bounding_box": {...},
        "age_range": {...},
        "gender": {...}
    }
}
```

## Environment Variables

- `AWS_DEFAULT_REGION`: AWS region for Rekognition (default: us-east-1)
- `AWS_ACCESS_KEY_ID`: AWS access key (if not using IAM roles)
- `AWS_SECRET_ACCESS_KEY`: AWS secret key (if not using IAM roles)

## Health Checks

The application includes a health check endpoint at `/health` that returns:
```json
{
    "status": "healthy",
    "service": "face-verification",
    "version": "1.0.0"
}
```

## Security Considerations

- The Docker image runs as a non-root user
- CORS is configured for web applications
- File size limits are enforced (20MB per image)
- Input validation for image formats
- AWS credentials should be managed via IAM roles in production
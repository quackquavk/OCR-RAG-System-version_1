# OCR-RAG System - Docker Deployment

This document provides instructions for building and running the OCR-RAG system using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose (optional, for easier deployment)
- Required configuration files in `app/config/`:
  - `serviceAccountKey.json` (Firebase)
  - `google_service_account.json` (Google Sheets)
  - `gemini-key.json` (Gemini API)
- `.env` file with environment variables

## Building the Docker Image

### Option 1: Using Docker Build

```bash
docker build -t ocr-rag-system:latest .
```

### Option 2: Using Docker Compose

```bash
docker-compose build
```

## Running the Container

### Option 1: Using Docker Run

```bash
dker run -doc \
  --name ocr-rag-system \
  -p 8000:8000 \
  -v ./media:/app/media \
  -v ./data:/app/data \
  -v ./counters.json:/app/counters.json \
  -v ./app/config:/app/app/config:ro \
  --env-file .env \
  ocr-rag-system:latest
```

### Option 2: Using Docker Compose (Recommended)

```bash
docker-compose up -d
```

## Accessing the Application

Once the container is running, access the application at:
- **API**: http://localhost:8000
- **Static Files**: http://localhost:8000/static/

## Managing the Container

### View Logs
```bash
docker logs -f ocr-rag-system
```

### Stop the Container
```bash
docker-compose down
# or
docker stop ocr-rag-system
```

### Restart the Container
```bash
docker-compose restart
# or
docker restart ocr-rag-system
```

## Volume Mounts

The following directories are mounted as volumes for data persistence:
- `./media` - Uploaded images and documents
- `./data` - Vector database and indexed documents
- `./counters.json` - Document counters
- `./app/config` - Configuration files (read-only)

## Environment Variables

Ensure your `.env` file contains all necessary environment variables for:
- Firebase configuration
- Google API keys
- Cloudinary credentials
- Other service configurations

## Troubleshooting

### Container Won't Start
- Check logs: `docker logs ocr-rag-system`
- Verify all config files exist in `app/config/`
- Ensure `.env` file is properly configured

### Port Already in Use
Change the port mapping in `docker-compose.yml` or use a different port:
```bash
docker run -p 8080:8000 ...
```

### Permission Issues
Ensure the mounted directories have proper permissions:
```bash
chmod -R 755 media data
```

## Image Size

Note: The Docker image is large (~3-4 GB) due to:
- PyTorch and ML dependencies
- Tesseract OCR
- EasyOCR models
- OpenCV libraries

## Production Deployment

For production deployment:
1. Use environment-specific `.env` files
2. Configure proper logging
3. Set up reverse proxy (nginx/traefik)
4. Enable HTTPS
5. Configure resource limits in docker-compose.yml

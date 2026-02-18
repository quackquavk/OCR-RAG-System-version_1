# 🐳 Docker Build & Push Guide

This guide will help you build your OCR-RAG System Docker image and push it to Docker Hub for deployment.

---

## 📋 Prerequisites

1. **Docker Desktop** installed and running
2. **Docker Hub account** (you have: `anil7777`)
3. **Terminal/PowerShell** access

---

## 🔐 Step 1: Login to Docker Hub

Open PowerShell and login to Docker Hub:

```powershell
docker login
```

Enter your Docker Hub credentials when prompted:
- **Username**: `anil7777`
- **Password**: Your Docker Hub password

> [!TIP]
> If you see "Login Succeeded", you're ready to proceed!

---

## 🏗️ Step 2: Build the Docker Image

Navigate to your project directory and build the image:

```powershell
cd C:\Users\Dell\Desktop\ocr_rag_system

# Build the image with your Docker Hub username
docker build -t anil7777/ocr-rag-system:latest .
```

**What this does:**
- `-t anil7777/ocr-rag-system:latest` - Tags the image with your username and version
- `.` - Uses the current directory (where Dockerfile is located)

> [!NOTE]
> This will take 5-10 minutes on first build as it downloads base images and installs dependencies (Tesseract, Python packages, etc.)

---

## 📤 Step 3: Push to Docker Hub

Once the build completes successfully, push the image:

```powershell
docker push anil7777/ocr-rag-system:latest
```

> [!IMPORTANT]
> The push may take 10-20 minutes depending on your internet speed. The image size will be approximately 2-3 GB due to Tesseract OCR and ML dependencies.

---

## ✅ Step 4: Verify the Push

Check if your image is available on Docker Hub:

1. Visit: https://hub.docker.com/r/anil7777/ocr-rag-system
2. Or run: `docker pull anil7777/ocr-rag-system:latest`

---

## 🔄 Optional: Tag Multiple Versions

If you want to maintain version tags:

```powershell
# Tag with version number
docker tag anil7777/ocr-rag-system:latest anil7777/ocr-rag-system:v1.0.0

# Push the versioned tag
docker push anil7777/ocr-rag-system:v1.0.0

# Push both tags
docker push anil7777/ocr-rag-system --all-tags
```

---

## 🧹 Cleanup Local Images (Optional)

After successful push, you can free up disk space:

```powershell
# Remove old/dangling images
docker image prune -f

# View all images
docker images
```

---

## 🚀 Next Steps: Deploy Your Image

Once pushed to Docker Hub, you can deploy on:

### **Option 1: Render**
1. Create new Web Service
2. Select "Deploy from Docker Hub"
3. Enter: `anil7777/ocr-rag-system:latest`
4. Add environment variables
5. Deploy!

### **Option 2: Railway**
```bash
railway login
railway init
railway up
```

### **Option 3: Fly.io**
```bash
fly launch --image anil7777/ocr-rag-system:latest
```

### **Option 4: Any Server with Docker**
```bash
docker pull anil7777/ocr-rag-system:latest
docker run -p 8000:8000 --env-file .env anil7777/ocr-rag-system:latest
```

---

## 🐛 Troubleshooting

### Build fails with "no space left on device"
```powershell
docker system prune -a
```

### Push fails with "denied: requested access to the resource is denied"
```powershell
docker logout
docker login
```

### Image too large
- Your image will be ~2-3 GB due to Tesseract OCR and ML libraries
- This is normal for OCR/ML applications
- Docker Hub free tier allows unlimited public repositories

---

## 📊 Image Size Breakdown

Your final image will include:
- **Base Python 3.11**: ~150 MB
- **Tesseract OCR + data**: ~500 MB
- **Python packages** (FastAPI, EasyOCR, sentence-transformers, etc.): ~1.5 GB
- **Application code**: ~10 MB
- **Total**: ~2-3 GB

> [!NOTE]
> This is optimized for functionality. Further size reduction would require removing features like EasyOCR or using lighter ML models.

---

## 🔒 Security Notes

> [!WARNING]
> Your Docker image should **NOT** include:
> - `.env` file (✅ Already in .dockerignore)
> - Service account JSON files (✅ Already in .dockerignore)
> - API keys or secrets

These should be passed at runtime via:
- Environment variables
- Volume mounts (for JSON files)
- Secrets management (in production)

Your `.dockerignore` is already configured correctly! ✅

---

## 📝 Quick Reference Commands

```powershell
# Build
docker build -t anil7777/ocr-rag-system:latest .

# Test locally before pushing
docker run -p 8000:8000 --env-file .env anil7777/ocr-rag-system:latest

# Push
docker push anil7777/ocr-rag-system:latest

# Pull (on deployment server)
docker pull anil7777/ocr-rag-system:latest
```

---

## ✨ All-in-One Script

Copy and run this in PowerShell:

```powershell
# Navigate to project
cd C:\Users\Dell\Desktop\ocr_rag_system

# Login to Docker Hub
docker login

# Build the image
docker build -t anil7777/ocr-rag-system:latest .

# Test the image locally (optional)
# docker run -p 8000:8000 --env-file .env anil7777/ocr-rag-system:latest

# Push to Docker Hub
docker push anil7777/ocr-rag-system:latest

# Verify
docker images | Select-String "ocr-rag-system"
```

---

**Ready to build and push?** Run the commands above and let me know if you encounter any issues! 🚀

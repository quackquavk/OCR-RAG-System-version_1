# 🐳 Docker Container Quick Reference

## Running the Container

### Option 1: Docker Compose (Recommended)

```bash
# Start container (foreground, see logs)
docker-compose up

# Start container (background)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop container
docker-compose down

# Restart container
docker-compose restart

# Rebuild and start
docker-compose up --build
```

---

### Option 2: Docker Run (Manual)

```bash
# Run with all mounts
docker run -d \
  --name ocr-rag-system \
  -p 8000:8000 \
  --env-file .env \
  -v ${PWD}/app/config:/app/app/config:ro \
  -v ${PWD}/media:/app/media \
  -v ${PWD}/data:/app/data \
  -v ${PWD}/counters.json:/app/counters.json \
  anil7777/ocr-rag-system:v4
```

**PowerShell version:**
```powershell
docker run -d `
  --name ocr-rag-system `
  -p 8000:8000 `
  --env-file .env `
  -v ${PWD}/app/config:/app/app/config:ro `
  -v ${PWD}/media:/app/media `
  -v ${PWD}/data:/app/data `
  -v ${PWD}/counters.json:/app/counters.json `
  anil7777/ocr-rag-system:v4
```

---

## Managing Containers

### View Running Containers
```bash
docker ps
```

### View All Containers (including stopped)
```bash
docker ps -a
```

### View Logs
```bash
# Real-time logs
docker logs -f ocr-rag-system

# Last 100 lines
docker logs --tail 100 ocr-rag-system
```

### Stop Container
```bash
docker stop ocr-rag-system
```

### Start Stopped Container
```bash
docker start ocr-rag-system
```

### Restart Container
```bash
docker restart ocr-rag-system
```

### Remove Container
```bash
docker rm ocr-rag-system

# Force remove (if running)
docker rm -f ocr-rag-system
```

---

## Accessing the Container

### Execute Commands Inside Container
```bash
# Open bash shell
docker exec -it ocr-rag-system bash

# Run Python command
docker exec ocr-rag-system python -c "print('Hello')"

# Check Python packages
docker exec ocr-rag-system pip list
```

### Copy Files To/From Container
```bash
# Copy from container to host
docker cp ocr-rag-system:/app/data/file.txt ./

# Copy from host to container
docker cp ./file.txt ocr-rag-system:/app/data/
```

---

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs ocr-rag-system

# Check if port is in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac
```

### Container Crashes Immediately
```bash
# Run in foreground to see errors
docker run --rm -p 8000:8000 --env-file .env anil7777/ocr-rag-system:v4

# Check health
docker inspect ocr-rag-system | grep -A 10 Health
```

### Credentials Not Found
```bash
# Verify volume mounts
docker inspect ocr-rag-system | grep -A 20 Mounts

# Check files inside container
docker exec ocr-rag-system ls -la /app/app/config/
```

### Reset Everything
```bash
# Stop and remove container
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Start fresh
docker-compose up
```

---

## Quick Access

Once running, access at:
- **Web Interface**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/

---

## Common Workflows

### Development (with hot-reload)
```bash
# Use docker-compose.yml (already configured for hot-reload)
docker-compose up
```

### Production (from Docker Hub)
```bash
# Pull latest image
docker pull anil7777/ocr-rag-system:latest

# Run container
docker run -d \
  --name ocr-rag-system \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  anil7777/ocr-rag-system:latest
```

### Update Container
```bash
# Pull new image
docker pull anil7777/ocr-rag-system:latest

# Stop and remove old container
docker stop ocr-rag-system
docker rm ocr-rag-system

# Run new container
docker run -d --name ocr-rag-system -p 8000:8000 --env-file .env anil7777/ocr-rag-system:latest
```

---

## Environment Variables

Container reads from:
1. `.env` file (via `--env-file .env`)
2. Individual `-e` flags: `-e ENVIRONMENT=production`
3. `docker-compose.yml` env_file section

---

## Volume Mounts Explained

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `./app/config/` | `/app/app/config/` | Credential files (read-only) |
| `./media/` | `/app/media/` | Uploaded files |
| `./data/` | `/app/data/` | Vector DB, processed data |
| `./counters.json` | `/app/counters.json` | Document counters |

---

## Health Check

Container has built-in health check:
```bash
# Check health status
docker inspect ocr-rag-system --format='{{.State.Health.Status}}'

# View health check logs
docker inspect ocr-rag-system --format='{{json .State.Health}}' | jq
```

---

## Resource Limits (Optional)

```bash
# Limit memory and CPU
docker run -d \
  --name ocr-rag-system \
  -p 8000:8000 \
  --memory="2g" \
  --cpus="2.0" \
  --env-file .env \
  anil7777/ocr-rag-system:v4
```

---

## Cleanup

### Remove Unused Images
```bash
docker image prune -a
```

### Remove All Stopped Containers
```bash
docker container prune
```

### Remove Everything (Nuclear Option)
```bash
docker system prune -a --volumes
```

---

**Recommended:** Use `docker-compose up` for local development! 🚀

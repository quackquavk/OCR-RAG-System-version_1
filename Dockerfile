# ===========================
# Stage 1: Builder
# ===========================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies and prune aggressively
RUN pip install -v --no-cache-dir --upgrade --force-reinstall --prefix=/install \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torch torchvision -r requirements.txt \
    && find /install -name "*.pyc" -delete \
    && find /install -name "__pycache__" -delete \
    # Remove all tests, examples, and documentation from site-packages
    && find /install/lib/python3.11/site-packages -type d -name "tests" -exec rm -rf {} + \
    && find /install/lib/python3.11/site-packages -type d -name "test" -exec rm -rf {} + \
    && find /install/lib/python3.11/site-packages -type d -name "examples" -exec rm -rf {} + \
    # Surgical pruning of Torch (~80MB total)
    # Preservation of torch_shm_manager is required for runtime
    && find /install/lib/python3.11/site-packages/torch/bin -type f ! -name "torch_shm_manager" -delete \
    && rm -rf /install/lib/python3.11/site-packages/torch/include \
    && rm -rf /install/lib/python3.11/site-packages/torch/lib/*.a \
    # Remove build tool packages but keep metadata (small but critical for some libs)
    && rm -rf /install/lib/python3.11/site-packages/pip \
    && rm -rf /install/lib/python3.11/site-packages/setuptools \
    && rm -rf /install/lib/python3.11/site-packages/wheel

# ===========================
# Stage 2: Final image
# ===========================
FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH="/usr/local/lib/python3.11/site-packages"

# Install ONLY runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/', timeout=5)" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

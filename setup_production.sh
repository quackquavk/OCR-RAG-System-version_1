#!/bin/bash
# =============================================================
#  Production Setup: systemd + Nginx + SSL for OCR-RAG-System
#  Domain : receipt.rebuzz.ai
#  App port: 9834
# =============================================================
set -euo pipefail

DOMAIN="receipt.rebuzz.ai"
APP_PORT="9834"
APP_DIR="/home/bbdevs/OCR-RAG-System-version_1"
VENV_DIR="$APP_DIR/.venv"
SERVICE_NAME="ocr-rag"
USER="bbdevs"
GROUP="bbdevs"

echo "==> [1/5] Creating systemd service..."

sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=OCR RAG System (FastAPI/Uvicorn)
After=network.target

[Service]
Type=simple
User=${USER}
Group=${GROUP}
WorkingDirectory=${APP_DIR}
Environment="PATH=${VENV_DIR}/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
EnvironmentFile=${APP_DIR}/.env
ExecStart=${VENV_DIR}/bin/uvicorn main:app --host 127.0.0.1 --port ${APP_PORT} --workers 2
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}

[Install]
WantedBy=multi-user.target
EOF

echo "==> [2/5] Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl start ${SERVICE_NAME}
sudo systemctl status ${SERVICE_NAME} --no-pager

echo "==> [3/5] Installing Nginx (if needed)..."
if ! command -v nginx &> /dev/null; then
    sudo apt update && sudo apt install -y nginx
fi

echo "==> [4/5] Configuring Nginx reverse proxy..."
sudo tee /etc/nginx/sites-available/${DOMAIN} > /dev/null <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # SSE / streaming support
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/${DOMAIN} /etc/nginx/sites-enabled/${DOMAIN}
# Remove default site if it exists
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

echo "==> [5/5] Setting up SSL with Let's Encrypt..."
if ! command -v certbot &> /dev/null; then
    sudo apt update && sudo apt install -y certbot python3-certbot-nginx
fi
sudo certbot --nginx -d ${DOMAIN} --non-interactive --agree-tos --redirect -m admin@rebuzz.ai

echo ""
echo "============================================="
echo "  ✅  Production setup complete!"
echo "============================================="
echo "  Domain  : https://${DOMAIN}"
echo "  App port: ${APP_PORT}"
echo "  Service : sudo systemctl status ${SERVICE_NAME}"
echo "  Logs    : sudo journalctl -u ${SERVICE_NAME} -f"
echo "============================================="

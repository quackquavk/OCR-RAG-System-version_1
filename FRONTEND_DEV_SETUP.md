# 🚀 Frontend Developer Backend Setup Guide

This guide helps frontend engineers run the OCR-RAG backend locally without needing to install Python, Tesseract, or complex dependencies.

## 📋 Prerequisites

1.  **Docker Desktop** installed and running.

## 📂 Required Files

Ask the backend developer (Anil) to send you a zip file properly containing the following structure. **These files contain secrets and are NOT in the git repo.**

```text
backend-setup/
├── docker-compose.prod.yml    (The docker composition file)
├── .env                       (Environment variables)
└── app/
    └── config/                (API Keys and Service Accounts)
        ├── serviceAccountKey.json
        ├── google_service_account.json
        └── gemini-key.json
```

## 🏃‍♂️ How to Run

1.  Unzip the folder you received.
2.  Open your terminal/command prompt in that folder.
3.  Run the following command:

```bash
docker-compose -f docker-compose.prod.yml up
```

**That's it!** Docker will automatically download the backend image (`anil7777/ocr-rag-system`) and start it.

## 🔍 Verification

- The API will be available at: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## 🛑 How to Stop

Press `Ctrl+C` in the terminal, or run:

```bash
docker-compose -f docker-compose.prod.yml down
```

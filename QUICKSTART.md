# 🚀 OCR RAG System - Quickstart Guide

This guide will help you set up and run the OCR RAG System, including configuring all necessary API keys and credentials.

## � Prerequisites

1.  **Docker Desktop** (Recommended) or Python 3.11+
2.  **Google Cloud Project**

## 🛠️ Step 1: Clone & Setup Config

Create a folder named `ocr-setup` and inside it, create the following structure:

```text
ocr-setup/
├── docker-compose.prod.yml   (Get this from the repo)
├── .env                      (Create properly)
└── app/
    └── config/               (Create this folder)
        ├── serviceAccountKey.json
        ├── google_service_account.json
        └── gemini-key.json
```

## � Step 2: Configure Credentials

You need to obtain critical keys for the system to work.

### 1. `.env` File
Create a `.env` file with these values:

```ini
# Security
JWT_SECRET=your_super_secret_string_here
ALLOWED_ORIGINS=*

# Google Cloud & AI
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_API_KEY=your_key_from_cloud_console
GEMINI_API_KEY=your_key_from_ai_studio

# OAuth (For Google Sheets)
GOOGLE_OAUTH_CLIENT_ID=your_oauth_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_oauth_client_secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/sheets/oauth/callback
```

### 2. app/config/serviceAccountKey.json (Firebase)
1. Go to [Firebase Console](https://console.firebase.google.com/) > Project Settings > Service accounts.
2. Click **Generate new private key**.
3. Rename the downloaded file to `serviceAccountKey.json` and place it in `app/config/`.

### 3. app/config/google_service_account.json (Google Cloud)
1. Go to [Google Cloud Console > IAM & Admin > Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts).
2. Create a service account.
3. Grant it **Editor** or specific roles (Sheets API, Drive API).
4. Create a JSON key for it.
5. Rename to `google_service_account.json` and place it in `app/config/`.

### 4. app/config/gemini-key.json (AI Studio)
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Create an API Key.
3. Create a file named `gemini-key.json` in `app/config/` with this content:
   ```json
   {
     "key": "YOUR_AI_STUDIO_KEY_HERE"
   }
   ```

## 🏃‍♂️ Step 3: Run with Docker (Easiest)

Once your config files are in place, run:

```bash
docker-compose -f docker-compose.prod.yml up
```

The API will start at `http://localhost:8000`.

## � Troubleshooting

- **"File not found" errors:** Ensure your folder structure matches Step 1 exactly.
- **"Permission denied" on Google Sheets:** Ensure you've enabled the **Google Sheets API** and **Google Drive API** in your Cloud Console.

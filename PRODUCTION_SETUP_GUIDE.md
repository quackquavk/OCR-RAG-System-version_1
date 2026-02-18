# 🚀 Production Deployment - Credentials Setup Guide

> **Complete guide for switching to a new Google account and configuring all credentials for production deployment**

---

## 📋 Table of Contents

1. [Google OAuth Credentials](#1-google-oauth-credentials)
2. [Google Service Account](#2-google-service-account)
3. [Firebase Credentials](#3-firebase-credentials)
4. [Gemini API Key](#4-gemini-api-key)
5. [Supabase Credentials](#5-supabase-credentials)
6. [Other API Keys](#6-other-api-keys)
7. [Production Environment Variables](#production-environment-variables)
8. [Deployment Checklist](#deployment-checklist)
9. [Security Best Practices](#security-best-practices)

---

## 🔐 Credentials You Need to Obtain

### 1. Google OAuth Credentials

**⚠️ MOST IMPORTANT FOR SWITCHING ACCOUNTS**

**What you need:**
- Google OAuth Client ID
- Google OAuth Client Secret
- OAuth Redirect URI (for production)

**Step-by-step instructions:**

#### Step 1: Access Google Cloud Console
- Visit: https://console.cloud.google.com/
- **Sign in with your NEW Google account**

#### Step 2: Create a New Project
- Click the project dropdown at the top
- Click **"New Project"**
- Project name: `OCR-RAG-Production` (or your preferred name)
- Click **"Create"**
- Wait for the project to be created (takes ~30 seconds)

#### Step 3: Enable Google Sheets API
- Go to **"APIs & Services"** → **"Library"**
- Search for **"Google Sheets API"**
- Click on it and press **"Enable"**
- Also enable **"Google Drive API"** (search and enable)

#### Step 4: Configure OAuth Consent Screen
- Go to **"APIs & Services"** → **"OAuth consent screen"**
- User Type: **External**
- Click **"Create"**
- Fill in required fields:
  - **App name:** OCR RAG System (or your app name)
  - **User support email:** Your NEW Google account email
  - **Developer contact email:** Your email
- Click **"Save and Continue"**

- **Scopes:** Click "Add or Remove Scopes"
  - Add: `../auth/spreadsheets`
  - Add: `../auth/drive.file`
  - Add: `../auth/userinfo.email`

- Click **"Save and Continue"**
- **Test users:** Add your email (optional for testing)
- Click **"Save and Continue"**

#### Step 5: Create OAuth 2.0 Credentials
- Go to **"APIs & Services"** → **"Credentials"**
- Click **"Create Credentials"** → **"OAuth client ID"**
- Application type: **Web application**
- Name: `OCR RAG Production`
- **Authorized redirect URIs:** Click "Add URI"
  ```
  https://your-production-domain.com/api/sheets/oauth/callback
  ```
  For local testing, also add:
  ```
  http://localhost:8000/api/sheets/oauth/callback
  ```
- Click **"Create"**
- **⚠️ IMPORTANT:** Copy and save:
  - **Client ID** (looks like: `xxxxx-xxxxxxx.apps.googleusercontent.com`)
  - **Client Secret** (looks like: `GOCSPX-xxxxxxxxx`)

**Add to .env:**
```env
GOOGLE_OAUTH_CLIENT_ID=<your-new-client-id>
GOOGLE_OAUTH_CLIENT_SECRET=<your-new-client-secret>
GOOGLE_OAUTH_REDIRECT_URI=https://your-production-domain.com/api/sheets/oauth/callback
```

---

### 2. Google Service Account

**What you need:**
- Service Account JSON file (`google_service_account.json`)

**Step-by-step instructions:**

#### Step 1: Create Service Account
- In Google Cloud Console (same project as above)
- Go to **"IAM & Admin"** → **"Service Accounts"**
- Click **"Create Service Account"**
- Service account name: `ocr-rag-service-account`
- Service account ID: (auto-generated)
- Click **"Create and Continue"**

#### Step 2: Grant Roles
- Select roles:
  - **Firebase Admin**
  - **Cloud Storage Admin** (if using Google Cloud Storage)
  - **Service Account Token Creator**
- Click **"Continue"**
- Click **"Done"**

#### Step 3: Create JSON Key
- Click on the service account you just created
- Go to **"Keys"** tab
- Click **"Add Key"** → **"Create new key"**
- Key type: **JSON**
- Click **"Create"**
- A JSON file will be downloaded automatically

#### Step 4: Save the File
- Rename the downloaded file to: `google_service_account.json`
- Move it to: `app/config/google_service_account.json`

**Add to .env:**
```env
GOOGLE_APPLICATION_CREDENTIALS=./app/config/google_service_account.json
```

---

### 3. Firebase Credentials

**What you need:**
- Firebase Admin SDK JSON file (`firebase-key.json`)

**Step-by-step instructions:**

#### Step 1: Access Firebase Console
- Visit: https://console.firebase.google.com/
- **Sign in with your NEW Google account**

#### Step 2: Create Firebase Project
- Click **"Add project"**
- Project name: Use the same name as your Google Cloud project
  - It should suggest linking to your existing GCP project
- Accept terms and click **"Continue"**
- **Google Analytics:** Enable or disable (your choice)
- Click **"Create project"**
- Wait for setup to complete

#### Step 3: Get Admin SDK Credentials
- Go to **Project Settings** (gear icon ⚙️ next to "Project Overview")
- Click **"Service accounts"** tab
- Click **"Generate new private key"**
- Click **"Generate key"** in the confirmation dialog
- A JSON file will be downloaded

#### Step 4: Save the File
- Rename the downloaded file to: `firebase-key.json`
- Move it to: `app/config/firebase-key.json`

**Add to .env:**
```env
FIREBASE_CREDENTIALS=./app/config/firebase-key.json
```

---

### 4. Gemini API Key

**What you need:**
- Gemini API Key (for Google AI)

**Step-by-step instructions:**

#### Step 1: Access Google AI Studio
- Visit: https://aistudio.google.com/app/apikey
- **Sign in with your NEW Google account**

#### Step 2: Create API Key
- Click **"Create API Key"**
- Select your Google Cloud project (the one you created earlier)
- Click **"Create API key in existing project"**
- **⚠️ IMPORTANT:** Copy and save the API key immediately
  - (looks like: `AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxx`)

**Add to .env:**
```env
GEMINI_API_KEY=<your-new-gemini-api-key>
GOOGLE_API_KEY=<your-new-gemini-api-key>
```

---

### 5. Supabase Credentials

**What you need:**
- Supabase URL
- Supabase Anon Key
- Storage Bucket

**Step-by-step instructions:**

#### Step 1: Access Supabase
- Visit: https://supabase.com/
- Click **"Start your project"**
- Sign in (can use your NEW Google account or GitHub)

#### Step 2: Create New Project
- Click **"New project"**
- Choose or create an organization
- Fill in project details:
  - **Name:** `ocr-rag-production`
  - **Database Password:** Create a strong password (save it!)
  - **Region:** Choose closest to your deployment location
  - **Pricing Plan:** Free or Pro (based on your needs)
- Click **"Create new project"**
- Wait 2-3 minutes for project setup

#### Step 3: Get API Credentials
- Go to **Project Settings** (gear icon) → **"API"**
- Copy and save:
  - **Project URL** (SUPABASE_URL)
    - Example: `https://xxxxxxxxxxxxx.supabase.co`
  - **Project API keys** → **anon/public** (SUPABASE_ANON_KEY)
    - Starts with `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

#### Step 4: Create Storage Bucket
- Go to **"Storage"** in left sidebar
- Click **"Create a new bucket"**
- Bucket details:
  - **Name:** `image`
  - **Public bucket:** ✅ Yes (if you want public access to images)
  - **File size limit:** 50MB (or as needed)
- Click **"Create bucket"**

#### Step 5: Enable Vector Extension (for RAG)
- Go to **"Database"** → **"Extensions"**
- Search for **"vector"**
- Enable **"pgvector"**

**Add to .env:**
```env
SUPABASE_URL=<your-supabase-url>
SUPABASE_ANON_KEY=<your-supabase-anon-key>
SUPABASE_BUCKET=image
VECTOR_STORE=supabase
```

---

### 6. Other API Keys

#### HuggingFace Token (Optional)
- Visit: https://huggingface.co/settings/tokens
- Sign in or create account
- Click **"New token"**
- Name: `ocr-rag-production`
- Role: **Read** (or Write if needed)
- Click **"Generate a token"**
- Copy and save the token

```env
HUGGINGFACEHUB_API_TOKEN=<your-hf-token>
```

#### Groq API Key (Optional)
- Visit: https://console.groq.com/
- Sign in or create account
- Go to **"API Keys"**
- Click **"Create API Key"**
- Copy and save

```env
GROQ_API_KEY=<your-groq-key>
```

#### DeepSeek API Key (Optional)
- Visit: https://platform.deepseek.com/
- Sign in or create account
- Go to API keys section
- Create new key
- Copy and save

```env
DEEPSEEK_API_KEY=<your-deepseek-key>
```

---

## 🌐 Production Environment Variables

### Complete `.env` Template for Production

```env
# ===========================================
# ENVIRONMENT
# ===========================================
ENVIRONMENT=production

# ===========================================
# JWT AUTHENTICATION
# ===========================================
SECRET_KEY=<generate-new-secure-key>
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ===========================================
# GOOGLE AI (GEMINI)
# ===========================================
GEMINI_API_KEY=<your-new-gemini-key>
GOOGLE_API_KEY=<your-new-gemini-key>

# ===========================================
# AI SERVICES (OPTIONAL)
# ===========================================
GROQ_API_KEY=<your-groq-key>
DEEPSEEK_API_KEY=<your-deepseek-key>
HUGGINGFACEHUB_API_TOKEN=<your-hf-token>
HUGGINGFACEHUB_API_TOKEN2=<your-hf-token2>

# ===========================================
# GOOGLE CLOUD & FIREBASE
# ===========================================
GOOGLE_APPLICATION_CREDENTIALS=./app/config/google_service_account.json
FIREBASE_CREDENTIALS=./app/config/firebase-key.json

# ===========================================
# SUPABASE (VECTOR DATABASE)
# ===========================================
SUPABASE_URL=<your-supabase-url>
SUPABASE_ANON_KEY=<your-supabase-anon-key>
SUPABASE_BUCKET=image
VECTOR_STORE=supabase

# ===========================================
# GOOGLE OAUTH (CRITICAL!)
# ===========================================
GOOGLE_OAUTH_CLIENT_ID=<your-new-oauth-client-id>
GOOGLE_OAUTH_CLIENT_SECRET=<your-new-oauth-client-secret>
GOOGLE_OAUTH_REDIRECT_URI=https://your-production-domain.com/api/sheets/oauth/callback

# ===========================================
# ENCRYPTION
# ===========================================
ENCRYPTION_KEY=<generate-new-key>

# ===========================================
# SERVER CONFIGURATION
# ===========================================
HOST=0.0.0.0
PORT=8000

# ===========================================
# CORS CONFIGURATION
# ===========================================
# ⚠️ DO NOT USE * IN PRODUCTION!
ALLOWED_ORIGINS=https://your-production-domain.com,https://www.your-production-domain.com

# ===========================================
# FRONTEND PAGE URLS
# ===========================================
UPLOAD_PAGE_URL=https://your-production-domain.com/static/upload_docs.html
SHEETS_PAGE_URL=https://your-production-domain.com/static/sheets.html
```

---

## 🔧 Generate Secure Keys

Run these commands locally to generate secure keys:

### Generate SECRET_KEY
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Generate ENCRYPTION_KEY
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## ✅ Deployment Checklist

### Pre-Deployment Tasks

- [ ] **Switch to NEW Google Account**
  - [ ] Create new Google Cloud project
  - [ ] Enable Google Sheets API
  - [ ] Enable Google Drive API
  - [ ] Configure OAuth consent screen
  - [ ] Create OAuth 2.0 credentials
  - [ ] Create Service Account
  - [ ] Download Service Account JSON

- [ ] **Firebase Setup**
  - [ ] Create Firebase project (link to GCP project)
  - [ ] Download Firebase Admin SDK JSON
  - [ ] Place JSON files in `app/config/`

- [ ] **API Keys**
  - [ ] Get new Gemini API key
  - [ ] Create/update Supabase project
  - [ ] Get Supabase URL and Anon Key
  - [ ] Create storage bucket in Supabase
  - [ ] Enable pgvector extension

- [ ] **Security**
  - [ ] Generate new SECRET_KEY for production
  - [ ] Generate new ENCRYPTION_KEY for production
  - [ ] Update ALLOWED_ORIGINS (remove `*`)
  - [ ] Set ENVIRONMENT=production

- [ ] **URLs & Redirects**
  - [ ] Update GOOGLE_OAUTH_REDIRECT_URI to production domain
  - [ ] Update UPLOAD_PAGE_URL to production domain
  - [ ] Update SHEETS_PAGE_URL to production domain

- [ ] **Files & Config**
  - [ ] Verify `google_service_account.json` exists in `app/config/`
  - [ ] Verify `firebase-key.json` exists in `app/config/`
  - [ ] Ensure `.env` is in `.gitignore`
  - [ ] **DO NOT** commit credential files to Git

### Deployment Platform Setup

- [ ] Choose deployment platform (Railway, Render, Vercel, etc.)
- [ ] Set environment variables in platform dashboard
- [ ] Upload credential JSON files securely (if supported)
- [ ] Configure custom domain (if applicable)
- [ ] Test OAuth flow after deployment

---

## 🔒 Security Best Practices

### Critical Security Rules

1. **Never Commit Secrets to Git**
   ```bash
   # Verify .gitignore includes:
   .env
   .env.*
   app/config/*.json
   ```

2. **Use Environment Variables in Deployment**
   - Don't hardcode credentials in code
   - Use platform-specific environment variable management
   - For JSON credentials, consider base64 encoding:
     ```bash
     # Encode
     cat app/config/google_service_account.json | base64
     
     # Then decode in your app startup
     ```

3. **Restrict CORS Origins**
   ```env
   # ❌ DON'T USE IN PRODUCTION:
   ALLOWED_ORIGINS=*
   
   # ✅ USE SPECIFIC DOMAINS:
   ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   ```

4. **Secure OAuth Redirects**
   - Only whitelist actual production URLs
   - Remove localhost URLs from production OAuth settings
   - Use HTTPS only (never HTTP in production)

5. **Rotate Keys Regularly**
   - Regenerate SECRET_KEY and ENCRYPTION_KEY periodically
   - Rotate API keys every 90 days
   - Revoke old credentials after migration

6. **Protect Credential Files**
   ```bash
   # Set proper file permissions (Linux/Mac):
   chmod 600 app/config/*.json
   ```

7. **Use Separate Accounts for Production**
   - Don't use personal Google accounts
   - Create dedicated service accounts
   - Use different credentials for dev/staging/prod

---

## 🚀 Deployment Platform Instructions

### Railway

1. **Create new project:**
   - Visit: https://railway.app/
   - Click "New Project" → "Deploy from GitHub repo"

2. **Set environment variables:**
   - Go to project → "Variables"
   - Click "New Variable"
   - Add all variables from `.env`
   
3. **Add credential files:**
   - Use Railway Files feature or base64 encode in env vars

4. **Deploy:**
   - Railway auto-deploys on git push

### Render

1. **Create new Web Service:**
   - Visit: https://render.com/
   - "New" → "Web Service"
   - Connect GitHub repo

2. **Configure:**
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Environment Variables:**
   - Go to "Environment" tab
   - Add all variables from `.env`
   - For credential files: use "Secret Files" feature

### Vercel (Serverless)

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Deploy:**
   ```bash
   vercel
   ```

3. **Set environment variables:**
   ```bash
   vercel env add GEMINI_API_KEY production
   # Repeat for all variables
   ```

---

## 📞 Support & Troubleshooting

### Common Issues

**OAuth Error: redirect_uri_mismatch**
- Solution: Ensure redirect URI in Google Cloud Console exactly matches your production URL

**Firebase Admin SDK Error**
- Solution: Verify JSON file path and ensure file is valid JSON

**Supabase Connection Error**
- Solution: Check URL format and ensure anon key is correct

**CORS Error**
- Solution: Add your frontend domain to ALLOWED_ORIGINS

### Testing Checklist

After deployment:
- [ ] Test OAuth flow (authorize Google Sheets access)
- [ ] Upload a document
- [ ] Verify file storage in Supabase
- [ ] Test RAG query functionality
- [ ] Check error logs for any credential issues

---

## 📝 Notes

- Keep this guide secure - it contains sensitive setup information
- Update this document when adding new services
- Document any platform-specific configuration changes
- Keep backup of all credential files in secure location (encrypted)

---

**Last Updated:** 2026-02-11  
**Version:** 1.0.0

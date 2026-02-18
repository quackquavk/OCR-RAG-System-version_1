# Google OAuth Setup Guide

This guide will help you set up Google OAuth for per-user Google Sheets integration.

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project name/ID

## Step 2: Enable Required APIs

1. In the Google Cloud Console, go to **APIs & Services** → **Library**
2. Search for and enable:
   - **Google Sheets API**
   - **Google Drive API**

## Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - User Type: **External** (for testing) or **Internal** (for organization only)
   - App name: `OCR RAG System`
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: Add `../auth/spreadsheets` and `../auth/drive.file`
   - Test users: Add your email and any test user emails
4. Back to **Create OAuth client ID**:
   - Application type: **Web application**
   - Name: `OCR RAG System Web Client`
   - Authorized redirect URIs: Add `http://localhost:8000/api/sheets/oauth/callback`
   - For production, also add your production URL (e.g., `https://yourdomain.com/api/sheets/oauth/callback`)
5. Click **CREATE**
6. **Download the JSON** or copy the **Client ID** and **Client Secret**

## Step 4: Generate Encryption Key

Run this command to generate an encryption key for storing OAuth tokens:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output (it will look like: `abcd1234efgh5678...=`)

## Step 5: Update .env File

Add these variables to your `.env` file:

```env
# Google OAuth Configuration
GOOGLE_OAUTH_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret_here
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/api/sheets/oauth/callback

# Encryption Key (generated in Step 4)
ENCRYPTION_KEY=your_encryption_key_here
```

## Step 6: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 7: Initialize Database

The new `user_google_sheets` table will be created automatically when you start the server:

```bash
uvicorn main:app --reload
```

## Step 8: Test the Flow

1. **Login** to your application
2. **Navigate** to the upload page
3. You should see a **"Connect Google Sheets"** button (upload will be blocked)
4. **Click** the button to start OAuth flow
5. **Sign in** with your Google account
6. **Grant permissions** to the app
7. A new spreadsheet will be created automatically
8. You'll be redirected back to the upload page
9. **Upload a document** - it will sync to YOUR Google Sheet!

## Troubleshooting

### "OAuth credentials not configured"

- Make sure `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` are in your `.env` file
- Restart the server after adding them

### "Redirect URI mismatch"

- The redirect URI in your `.env` must EXACTLY match what's configured in Google Cloud Console
- Check for http vs https, trailing slashes, etc.

### "Access blocked: This app's request is invalid"

- Make sure you've added your email as a test user in the OAuth consent screen
- Check that the required scopes are configured

### "Token refresh failed"

- The refresh token might be invalid
- Disconnect and reconnect Google Sheets from the UI

## Production Deployment

For production:

1. Update `GOOGLE_OAUTH_REDIRECT_URI` to your production URL
2. Add the production redirect URI to Google Cloud Console
3. Consider moving OAuth consent screen from "Testing" to "Published"
4. Use a secure method to store `ENCRYPTION_KEY` (e.g., AWS Secrets Manager)
5. Enable HTTPS for your application

## Security Notes

- OAuth tokens are encrypted before storage using Fernet encryption
- Tokens are automatically refreshed when expired
- Each user has their own isolated Google Sheet
- Users can disconnect their Google Sheets at any time via `/api/sheets/disconnect`


## GOOGLE_API_KEY (For Google Sheets/Drive & Search)
Where: Google Cloud Console
Steps:
Go to APIs & Services > Credentials.
Click + CREATE CREDENTIALS at the top.
Select API Key.
Copy the generated key.

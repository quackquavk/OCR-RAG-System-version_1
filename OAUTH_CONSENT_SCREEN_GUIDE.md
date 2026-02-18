# OAuth Consent Screen Configuration - Step-by-Step Guide

## When Does This Appear?

When you try to create OAuth credentials for the first time, Google will prompt you to configure the OAuth consent screen. This is the screen users see when they're asked to grant permissions to your app.

## Step-by-Step Instructions

### Step 1: Access OAuth Consent Screen

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project from the dropdown at the top
3. In the left sidebar, click **APIs & Services** → **OAuth consent screen**

### Step 2: Choose User Type

You'll see two options:

**Option A: Internal** (Recommended if you have a Google Workspace)
- Only users in your organization can use the app
- No verification required
- Choose this if you're the only user or all users are in your organization

**Option B: External** (Recommended for testing/personal use)
- Anyone with a Google account can use the app
- Requires verification for production (but not for testing)
- Choose this for personal projects or if users are outside your organization

**For testing, choose "External"** and click **CREATE**.

---

### Step 3: App Information

Fill in the following fields:

#### Required Fields:

**App name:**
```
OCR RAG System
```

**User support email:**
- Select your email from the dropdown
- This is where users can contact you for support

**App logo:** (Optional)
- Skip this for now
- You can add it later if needed

**Application home page:** (Optional)
- Leave blank for now
- Or enter: `http://localhost:8000`

**Application privacy policy link:** (Optional)
- Leave blank for testing
- Required for production

**Application terms of service link:** (Optional)
- Leave blank for testing

#### Developer Contact Information:

**Email addresses:**
- Enter your email address
- This is for Google to contact you about your app

Click **SAVE AND CONTINUE**.

---

### Step 4: Scopes

This is where you specify what permissions your app needs.

1. Click **ADD OR REMOVE SCOPES**
2. In the search box or filter, look for these scopes:

**Scope 1: Google Sheets**
- Search for: `spreadsheets`
- Check the box for: **`.../auth/spreadsheets`**
- Description: "See, edit, create, and delete all your Google Sheets spreadsheets"

**Scope 2: Google Drive (File Access)**
- Search for: `drive.file`
- Check the box for: **`.../auth/drive.file`**
- Description: "See, edit, create, and delete only the specific Google Drive files you use with this app"

3. Click **UPDATE** at the bottom
4. Verify both scopes are listed in the "Your non-sensitive scopes" section
5. Click **SAVE AND CONTINUE**

---

### Step 5: Test Users (External Only)

If you chose "External" user type, you need to add test users:

1. Click **+ ADD USERS**
2. Enter email addresses (one per line):
   ```
   your.email@gmail.com
   friend.email@gmail.com
   ```
3. Click **ADD**
4. Click **SAVE AND CONTINUE**

> [!IMPORTANT]
> **Only these test users can use your app while it's in "Testing" mode.**
> Add any email addresses that need to test the OAuth flow.

---

### Step 6: Summary

Review your settings:
- App name: OCR RAG System
- User type: External
- Scopes: 2 scopes added
- Test users: X users added

Click **BACK TO DASHBOARD**.

---

## Now Create OAuth Credentials

After configuring the consent screen, you can create OAuth credentials:

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Application type: **Web application**
4. Name: `OCR RAG System Web Client`
5. Authorized redirect URIs:
   - Click **+ ADD URI**
   - Enter: `http://localhost:8000/api/sheets/oauth/callback`
6. Click **CREATE**
7. **Copy the Client ID and Client Secret** and save them to your `.env` file

---

## Visual Reference

### What the OAuth Consent Screen Looks Like to Users:

When users click "Connect Google Sheets", they'll see:

```
┌─────────────────────────────────────────┐
│  Google                                 │
│                                         │
│  OCR RAG System wants to access your    │
│  Google Account                         │
│                                         │
│  your.email@gmail.com                   │
│                                         │
│  This will allow OCR RAG System to:     │
│                                         │
│  ✓ See, edit, create, and delete all    │
│    your Google Sheets spreadsheets      │
│                                         │
│  ✓ See, edit, create, and delete only   │
│    the specific Google Drive files you  │
│    use with this app                    │
│                                         │
│  [ Cancel ]  [ Continue ]               │
└─────────────────────────────────────────┘
```

---

## Troubleshooting

### "This app isn't verified"

If you see this warning:
1. This is normal for apps in "Testing" mode
2. Click **Advanced** → **Go to OCR RAG System (unsafe)**
3. This only appears for test users
4. For production, you'd need to verify the app with Google

### Can't find the scopes

Make sure you've enabled the APIs first:
1. Go to **APIs & Services** → **Library**
2. Search for "Google Sheets API" and enable it
3. Search for "Google Drive API" and enable it
4. Then go back to configure scopes

### "Access blocked: This app's request is invalid"

- Make sure you added your email as a test user
- Make sure the redirect URI matches exactly: `http://localhost:8000/api/sheets/oauth/callback`
- Check that both required scopes are added

---

## Quick Checklist

- [ ] OAuth consent screen configured
- [ ] User type selected (External for testing)
- [ ] App name: "OCR RAG System"
- [ ] Support email added
- [ ] Developer contact email added
- [ ] Scopes added: `../auth/spreadsheets` and `../auth/drive.file`
- [ ] Test users added (your email at minimum)
- [ ] OAuth credentials created
- [ ] Client ID and Secret copied to `.env` file

---

## Next Steps

After completing this:
1. Add the credentials to your `.env` file:
   ```env
   GOOGLE_OAUTH_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
   GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret_here
   ```
2. Generate an encryption key
3. Restart your server
4. Test the OAuth flow!

# OCR RAG System: API Documentation

This guide details the API endpoints available in the `app/presentation` layer of the OCR RAG System, specifically designed for frontend integration (Next.js).

**Base URL:** `http://localhost:8000` (or your deployed URL)

## Authentication

All endpoints (unless otherwise specified) require authentication via **Firebase**.

- **Header:** `Authorization: Bearer <firebase_id_token>`
- **Token Payload:** Must contain `userId` (or `uid`), `activeCompany`, and `companyName` (handled by backend middleware).
- **Multi-tenancy:** All data is isolated by user and company. Each user can belong to multiple companies, and data is strictly separated per company.

---

## 1. Document Processing

### Upload & Process Image

Uploads an image or PDF for OCR processing, parsing, and storage. Supports both images (PNG, JPG, etc.) and PDF files.

- **Endpoint:** `/process-image`
- **Method:** `POST`
- **File:** `app/presentation/upload_routes.py`
- **Authentication:** Required

#### Request

- **Body:** `multipart/form-data`
  - `file`: The binary file (image or PDF).

#### Response

```json
{
  "status": "success",
  "image_url": "http://127.0.0.1:8000/media/uploads/Receipt_20231027120000.png",
  "document_key": "unique_doc_id",
  "parsed": {
    "total_amount": 100.0,
    "date": "2023-10-27",
    "merchant": "Example Store",
    "items": [
      {
        "name": "Item 1",
        "quantity": 2,
        "price": 50.0
      }
    ]
  },
  "categorization": {
    "category": "Office Supplies",
    "confidence": 0.95
  }
}
```

#### Features

- **OCR Processing:** Extracts text from images and PDFs using Tesseract OCR
- **AI Parsing:** Uses Gemini AI to parse and structure the extracted data
- **Categorization:** Automatically categorizes transactions
- **Vector Indexing:** Indexes documents in background for RAG search
- **Google Sheets Sync:** Automatically syncs to connected Google Sheets (if configured)
- **Multi-tenant:** Data is isolated by user and company

#### Next.js Example

```tsx
const uploadDocument = async (file: File, token: string) => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/process-image`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  if (!res.ok) {
    throw new Error(`Upload failed: ${res.statusText}`);
  }

  return res.json();
};
```

#### Error Responses

- **400 Bad Request:** Invalid file format or empty OCR text
- **500 Internal Server Error:** Processing failed

---

## 2. Search & Retrieval

### Search Documents

Retrieve a list of processed documents with optional filtering. Returns only documents belonging to the authenticated user and their active company.

- **Endpoint:** `/search-documents`
- **Method:** `GET`
- **File:** `app/presentation/search_routes.py`
- **Authentication:** Required

#### Query Parameters

- `start_date` (optional): Filter by start date in `YYYY-MM-DD` format
- `end_date` (optional): Filter by end date in `YYYY-MM-DD` format
- `doc_type` (optional): Filter by document type - `receipt`, `invoice`, `bank_statement`, `others`, or `all`

#### Response

```json
[
  {
    "doc_id": "unique_doc_id",
    "created_at": "2023-10-27T10:00:00Z",
    "image_url": "http://127.0.0.1:8000/media/uploads/Receipt_20231027120000.png",
    "document_type": "receipt"

  }
]
```

#### Next.js Example

```tsx
const searchDocuments = async (
  token: string,
  filters?: {
    start_date?: string;
    end_date?: string;
    doc_type?: string;
  }
) => {
  const params = new URLSearchParams();
  if (filters?.start_date) params.append("start_date", filters.start_date);
  if (filters?.end_date) params.append("end_date", filters.end_date);
  if (filters?.doc_type) params.append("doc_type", filters.doc_type);

  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/search-documents?${params}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    }
  );

  return res.json();
};
```

---

## 3. Data Export

### Generate CSV

Download a single document's data as a CSV file. Excludes internal system fields (company_id, image_url, document_key, user_id, created_at, document_type).

- **Endpoint:** `/generate-csv/{doc_id}`
- **Method:** `GET`
- **File:** `app/presentation/csv_routes.py`
- **Authentication:** Required

#### Path Parameters

- `doc_id`: The unique document identifier

#### Response

```json
{
  "doc_id": "unique_doc_id",
  "csv": "Date,Amount,Merchant\n2023-10-27,100.0,Example Store",
  "filename": "unique_doc_id.csv"
}
```

#### Next.js Example

```tsx
const downloadCSV = async (docId: string, token: string) => {
  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/generate-csv/${docId}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    }
  );

  const data = await res.json();

  // Create and download CSV file
  const blob = new Blob([data.csv], { type: "text/csv" });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = data.filename;
  a.click();
};
```

---

### Generate Excel

Download a single document's data as a beautifully formatted Excel file with professional styling and templates.

- **Endpoint:** `/generate-excel/{doc_id}`
- **Method:** `GET`
- **File:** `app/presentation/csv_routes.py`
- **Authentication:** Required

#### Path Parameters

- `doc_id`: The unique document identifier

#### Response

Returns an Excel file (`.xlsx`) as a binary download with proper formatting:

- **Content-Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Content-Disposition:** `attachment; filename="receipt_unique_doc_id.xlsx"`

#### Features

- Professional table formatting with headers and borders
- Document-type specific templates (invoice, receipt, bank statement)
- Standardized structure with columns: S.N, Items, Quantity, Price per Unit, Total
- Invoice details displayed in left column (date, invoice number, customer info)
- Excludes internal system fields
- Beautiful styling with colors and fonts

#### Next.js Example

```tsx
const downloadExcel = async (docId: string, token: string) => {
  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/generate-excel/${docId}`,
    {
      headers: { Authorization: `Bearer ${token}` },
    }
  );

  if (!res.ok) {
    throw new Error("Failed to generate Excel");
  }

  // Get filename from Content-Disposition header
  const contentDisposition = res.headers.get("Content-Disposition");
  const filename =
    contentDisposition?.match(/filename="(.+)"/)?.[1] || `${docId}.xlsx`;

  // Download the file
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
};
```

---

## 4. AI Chat (RAG)

### Chat with Documents

Ask questions about your uploaded documents using Retrieval-Augmented Generation. The AI retrieves relevant documents and generates intelligent responses based on your data.

- **Endpoint:** `/api/chat`
- **Method:** `POST`
- **File:** `app/presentation/chat_routes.py`
- **Authentication:** Required

#### Request

```json
{
  "query": "How much did I spend on office supplies last month?"
}
```

#### Response

Returns a JSON object with the AI's answer based on your document context. The response includes:

- The AI-generated answer
- Relevant document excerpts used to generate the answer
- Source document references

```json
{
  "answer": "Based on your documents, you spent $450.00 on office supplies last month.",
  "sources": [
    {
      "document_key": "doc_123",
      "excerpt": "Office Supplies - $450.00",
      "date": "2023-10-15"
    }
  ]
}
```

#### Features

- **User & Company Isolation:** Only searches documents belonging to the authenticated user and their active company
- **Vector Search:** Uses semantic search to find relevant documents
- **Context-Aware:** Provides answers based on actual document data
- **Source Attribution:** Shows which documents were used to generate the answer

#### Next.js Example

```tsx
const sendChat = async (query: string, token: string) => {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/chat`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query }),
  });

  if (!res.ok) {
    throw new Error("Chat request failed");
  }

  return res.json();
};
```

#### Error Responses

- **500 Internal Server Error:** Chat processing failed

---

## 5. Google Sheets Integration

### Check Connection Status

Check if the current user/company has linked a Google Sheet. Each user-company combination has its own separate Google Sheet connection.

- **Endpoint:** `/api/sheets/status`
- **Method:** `GET`
- **File:** `app/presentation/sheet_routes.py`
- **Authentication:** Required

#### Response

```json
{
  "connected": true,
  "spreadsheet_name": "AI Receipt - Company 123",
  "spreadsheet_id": "1abc...",
  "spreadsheet_url": "https://docs.google.com/spreadsheets/d/1abc..."
}
```

Or if not connected:

```json
{
  "connected": false
}
```

#### Next.js Example

```tsx
const checkSheetsStatus = async (token: string) => {
  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/api/sheets/status`,
    {
      headers: { Authorization: `Bearer ${token}` },
    }
  );

  return res.json();
};
```

---

### Connect Sheet

Initiate OAuth flow to connect Google Sheets for the current user and their active company.

- **Endpoint:** `/api/sheets/connect`
- **Method:** `GET`
- **File:** `app/presentation/sheet_routes.py`
- **Authentication:** Required

#### Response

```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?client_id=...&redirect_uri=...&state=user123:company456"
}
```

#### Usage

Redirect the user's browser to the `auth_url` to initiate the Google OAuth flow.

#### Next.js Example

```tsx
const connectGoogleSheets = async (token: string) => {
  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/api/sheets/connect`,
    {
      headers: { Authorization: `Bearer ${token}` },
    }
  );

  const data = await res.json();

  // Redirect user to Google OAuth
  window.location.href = data.auth_url;
};
```

---

### OAuth Callback

Handles the redirect from Google after the user authorizes the application. This endpoint is called automatically by Google's OAuth flow.

- **Endpoint:** `/api/sheets/oauth/callback`
- **Method:** `GET`
- **File:** `app/presentation/sheet_routes.py`
- **Authentication:** Not required (uses state parameter for user identification)

#### Query Parameters

- `code`: Authorization code from Google
- `state`: User and company identifier in format `user_id:company_id`
- `error`: Error code if user denied access

#### Behavior

- **Success:** Creates a company-specific spreadsheet and redirects to `/static/upload_docs.html?sheets_connected=true&sheet_name=AI Receipt - Company 123`
- **User Cancelled:** Redirects to `/static/upload_docs.html?sheets_cancelled=true`
- **Error:** Redirects to `/static/upload_docs.html?sheets_error=true&error=...`

#### Features

- **Per User-Company Connection:** Each user needs separate sheet connections for each company they belong to
- **Data Isolation:** Complete data isolation between companies
- **Automatic Spreadsheet Creation:** Creates a new spreadsheet with company-specific name
- **Token Encryption:** Access and refresh tokens are encrypted before storage
- **Auto-Sync:** Once connected, new documents are automatically synced to the Google Sheet

---

## Additional Notes

### Multi-Tenancy

All endpoints enforce strict multi-tenancy:

- Data is isolated by both `user_id` and `company_id`
- Users can belong to multiple companies
- Each user-company combination has separate data and configurations
- Google Sheets connections are per user-company combination

### Error Handling

All endpoints follow standard HTTP status codes:

- **200 OK:** Request successful
- **400 Bad Request:** Invalid input or validation error
- **401 Unauthorized:** Missing or invalid authentication token
- **404 Not Found:** Resource not found
- **500 Internal Server Error:** Server-side error

### CORS

The API has CORS enabled for all origins (`*`). In production, you should restrict this to your frontend domain.

### Media Files

Uploaded files are served from `/media/uploads/` and are accessible via:

```
http://localhost:8000/media/uploads/Receipt_20231027120000.png
```

---

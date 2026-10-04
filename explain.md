# DocuFlow AI — Project Explanation

> **An AI-powered Document Processing & Workflow Automation System**  
> Built as a full-stack web application to automate the intake, classification, data extraction, and downstream processing of business documents.

---

## 📌 1. What is DocuFlow AI?

DocuFlow AI is an **intelligent document processing (IDP) platform** that automates the end-to-end lifecycle of business documents — from the moment a user uploads a file (PDF, image) to the extraction of structured data, confidence-based human review, and trigger-based workflow automation.

### The Problem It Solves

In large enterprises like **Torrent Power**, thousands of documents flow through departments daily — invoices from vendors, KYC forms from customers, employee resumes, purchase receipts, and ID cards. Manually reading, classifying, and entering data from these documents into systems is:

- **Slow** — A single clerk might process 50–100 documents per day
- **Error-prone** — Typos, missed fields, misclassification
- **Expensive** — Requires dedicated staff for data entry
- **Non-scalable** — Backlogs grow during peak periods (e.g., billing cycles)

DocuFlow AI eliminates this bottleneck by automating the entire pipeline.

---

## 🏗️ 2. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + Vite)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐│
│  │Dashboard │ │ Upload   │ │Documents │ │ Review   │ │Workflow││
│  │(Stats &  │ │(Drag &   │ │(List &   │ │(Verify & │ │(Rules &││
│  │ Charts)  │ │ Drop)    │ │ Filter)  │ │ Approve) │ │ Logs)  ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘│
└────────────────────────────┬─────────────────────────────────────┘
                             │ REST API (Axios + JWT)
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI + Python)                  │
│                                                                  │
│  ┌─────────────────────── Processing Pipeline ──────────────────┐│
│  │                                                              ││
│  │  Upload ──► OCR/Text ──► Classify ──► Extract ──► Confidence ││
│  │              Extract      Document     Fields      Scoring   ││
│  │                                                      │       ││
│  │                                          ┌───────────┴──┐    ││
│  │                                          ▼              ▼    ││
│  │                                    High Confidence  Low Conf ││
│  │                                    (Auto-complete)  (Review) ││
│  │                                          │                   ││
│  │                                          ▼                   ││
│  │                                   Workflow Engine            ││
│  │                                   (Email/Slack/              ││
│  │                                    Google Sheets)            ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Auth    │  │  Models  │  │ Services │  │   Integrations   │ │
│  │  (JWT +  │  │  (SQLAlch│  │  (OCR,   │  │  (SMTP, Slack,   │ │
│  │  bcrypt) │  │  emy ORM)│  │  AI, NLP)│  │   Google Sheets) │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└──────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   SQLite / Postgres │
                    │     (Database)      │
                    └─────────────────────┘
```

---

## 🛠️ 3. Tech Stack

| Layer          | Technology                | Why I Chose It                                         |
|----------------|---------------------------|-------------------------------------------------------|
| **Frontend**   | React 18 + Vite           | Fast HMR, modern JSX, component-based UI              |
| **Styling**    | Tailwind CSS 3            | Rapid UI development with utility classes             |
| **Charts**     | Recharts                  | Interactive pie/bar charts for the dashboard          |
| **HTTP Client**| Axios                     | Promise-based, interceptors for JWT auto-attachment   |
| **Routing**    | React Router DOM v6       | Nested routes, protected route pattern                |
| **Backend**    | FastAPI (Python)          | Async support, auto-generated OpenAPI docs, type-safe |
| **ORM**        | SQLAlchemy 2.0            | Mature, supports multiple databases                   |
| **Auth**       | JWT (python-jose) + bcrypt| Stateless authentication, secure password hashing     |
| **OCR**        | Tesseract (pytesseract)   | Open-source, industry-standard OCR engine             |
| **PDF Parsing**| PyMuPDF + pdfplumber      | Dual-fallback PDF text extraction                     |
| **Image Proc.**| Pillow + OpenCV           | Image pre-processing before OCR                       |
| **AI (Optional)**| OpenAI GPT-4o-mini     | Enhanced extraction when API key is available         |
| **Database**   | SQLite (dev) / PostgreSQL (prod) | Zero-config dev, enterprise-grade production   |
| **Deployment** | Docker + Docker Compose   | Consistent dev/prod environments                     |
| **Logging**    | Loguru                    | Structured, colored, file-rotated logging             |

---

## 🔄 4. Document Processing Pipeline (The Core Logic)

This is the heart of the project. When a user uploads a document, a **6-step background pipeline** kicks in:

### Step 1: File Upload & Validation
```
User uploads file ──► Validate (size ≤ 20MB, type ∈ {pdf, png, jpg, jpeg})
                  ──► Generate secure filename (UUID-based)
                  ──► Save to /uploads directory
                  ──► Create DB record with status = "UPLOADED"
                  ──► Trigger background processing task
```

### Step 2: Text Extraction (OCR Service)
The system uses a **multi-strategy extraction approach**:

| Document Type | Primary Strategy         | Fallback Strategy           |
|---------------|--------------------------|----------------------------|
| PDF (digital) | PyMuPDF (embedded text)  | pdfplumber                 |
| PDF (scanned) | PyMuPDF → detect empty → | Tesseract OCR (page-by-page render at 144 DPI) |
| Image (PNG/JPG)| Tesseract OCR directly  | —                          |

**Key Design Decision:** Real extraction is always attempted first. Demo/fake data is only used when `DEMO_MODE=true` AND real extraction has already failed.

### Step 3: Document Classification
Uses a **rule-based scoring system** (no ML dependency = predictable, explainable):

```python
# Each document type gets scored based on keyword presence
scores = {
    "invoice":  0,  # +6 for "invoice", +3 for "bill to", "subtotal"
    "resume":   0,  # +6 for "resume"/"CV", +2 for "experience", "skills"
    "kyc":      0,  # +6 for "KYC", +3 for "aadhaar", "pan"
    "receipt":  0,  # +6 for "receipt", +2 for "merchant", "cashier"
    "id_card":  0,  # +6 for "identity card", +2 for "date of birth"
}
# Highest score wins → document_type assigned
```

**Supported Document Types:**
1. **Invoice** — Vendor bills, purchase orders
2. **Resume/CV** — Job applications
3. **KYC** — Know Your Customer forms (Aadhaar, PAN-based)
4. **Receipt** — Purchase receipts, transaction records
5. **ID Card** — Passport, Aadhaar card, driving license

### Step 4: Field Extraction
**This is the most complex service** (~780 lines). It uses deterministic regex-based heuristics tailored per document type:

**For Invoices:**
| Field            | Extraction Method                              | Confidence |
|------------------|-------------------------------------------------|-----------|
| Invoice Number   | Regex: `invoice\s*(?:number\|no\|#)\s*[:#-]?\s*…` | 0.97      |
| Invoice Date     | Label-anchored date search                      | 0.95      |
| Due Date         | Label-anchored date search                      | 0.93      |
| Total Amount     | Currency-aware amount regex                     | 0.96      |
| Vendor Name      | Label search + first-line heuristic             | 0.90      |
| Customer Name    | "Bill To" label extraction                      | 0.90      |
| Currency         | Symbol/code detection (₹, $, INR, USD)          | 0.85      |

**For Resumes:**
| Field     | Extraction Method                    | Confidence |
|-----------|---------------------------------------|-----------|
| Name      | First non-title line heuristic        | 0.86      |
| Email     | Email regex pattern                   | 0.99      |
| Phone     | Phone regex with validation           | 0.94      |
| Skills    | Section heading extraction            | 0.88      |
| LinkedIn  | URL pattern matching                  | 0.97      |

**For KYC Documents:**
| Field         | Extraction Method              | Confidence |
|---------------|--------------------------------|-----------|
| Name          | Label-value pair parsing       | 0.88      |
| Date of Birth | Date pattern near DOB labels   | 0.96      |
| ID Type       | Label extraction               | 0.92      |
| ID Number     | Alphanumeric pattern + masking | 0.91      |
| Address       | Multi-line address detection   | 0.86      |

### Step 5: Confidence Scoring
Each extracted field gets a confidence score (0.0 to 1.0):

| Level    | Score Range | Action              |
|----------|-------------|---------------------|
| **High** | ≥ 0.95      | Auto-accepted       |
| **Medium**| ≥ 0.75     | Accepted, flagged   |
| **Low**  | < 0.75      | → **REVIEW_REQUIRED** (human review) |

If any field has low confidence OR the document type is "unknown", the entire document is routed to human review.

### Step 6: Workflow Execution
After successful processing (or manual approval), the **Workflow Engine** evaluates rule-based automations:

```
Workflow Rule Example:
├── Document Type: invoice
├── Condition: total_amount > 50000
└── Actions:
    ├── Send email to finance@company.com
    ├── Post Slack notification to #approvals
    └── Log to Google Sheets
```

The engine supports operators: `==`, `!=`, `>`, `<`, `>=`, `<=`, `contains`

---

## 💾 5. Database Design

```
┌──────────────┐       ┌──────────────────┐       ┌─────────────────┐
│    users     │       │    documents     │       │extracted_fields │
├──────────────┤       ├──────────────────┤       ├─────────────────┤
│ id (PK)      │──┐    │ id (PK)          │──┐    │ id (PK)         │
│ name         │  │    │ user_id (FK)     │  │    │ document_id(FK) │
│ email (UNQ)  │  │    │ file_name        │  │    │ field_name      │
│ password_hash│  └───►│ file_path        │  └───►│ field_value     │
│ is_active    │       │ file_type        │       │ confidence_score│
│ created_at   │       │ document_type    │       │ is_verified     │
└──────────────┘       │ status           │       │ verified_value  │
                       │ extracted_text   │       │ created_at      │
                       │ processing_time  │       └─────────────────┘
                       │ error_message    │
                       │ uploaded_at      │       ┌─────────────────┐
                       │ processed_at     │       │  workflow_logs  │
                       └──────────────────┘       ├─────────────────┤
                                                  │ id (PK)         │
┌──────────────┐                                  │ document_id(FK) │
│  workflows   │──────────────────────────────────►│ workflow_id(FK) │
├──────────────┤                                  │ action          │
│ id (PK)      │                                  │ status          │
│ name         │                                  │ message         │
│ document_type│                                  │ retry_count     │
│ conditions   │ (JSON)                           │ timestamp       │
│ actions      │ (JSON)                           └─────────────────┘
│ enabled      │
│ require_appr │
│ created_at   │
└──────────────┘
```

**Key Relationships:**
- `User` → has many `Documents` (one-to-many, cascade delete)
- `Document` → has many `ExtractedFields` (one-to-many, cascade delete)
- `Document` → has many `WorkflowLogs` (one-to-many, cascade delete)
- `Workflow` → has many `WorkflowLogs` (one-to-many, cascade delete)

---

## 🖥️ 6. Frontend Pages

| Page                | Purpose                                             | Key Features                          |
|---------------------|-----------------------------------------------------|---------------------------------------|
| **Login/Register**  | User authentication                                | JWT-based, form validation            |
| **Dashboard**       | Overview stats & analytics                          | Stat cards, pie chart (Recharts), recent docs table |
| **Upload**          | Drag-and-drop document upload                       | react-dropzone, file type validation  |
| **Documents**       | Paginated document list with status filters          | Status badges, search, pagination     |
| **Document Review** | View extracted fields, correct values, approve       | Inline editing, confidence indicators, approve button |
| **Workflows**       | Create/manage automation rules                       | JSON-based condition builder, action config |

---

## 🔐 7. Security Features

| Feature                    | Implementation                                   |
|----------------------------|--------------------------------------------------|
| **Password Storage**       | bcrypt hashing (never stored in plain text)       |
| **Authentication**         | JWT tokens with 24-hour expiry                   |
| **API Authorization**      | Token-based middleware on all protected routes     |
| **File Upload Security**   | UUID-based secure filenames (prevents path traversal) |
| **File Validation**        | Extension whitelist + size limit (20 MB)          |
| **Sensitive Data Masking** | ID numbers are masked in logs (e.g., `XXXX 4567`) |
| **CORS**                   | Configurable allowed origins                      |
| **SQL Injection**          | SQLAlchemy ORM parameterized queries              |

---

## 🔌 8. API Endpoints

| Method | Endpoint                                    | Description                    |
|--------|---------------------------------------------|--------------------------------|
| POST   | `/api/auth/register`                        | Create new user account        |
| POST   | `/api/auth/login`                           | Login, returns JWT token       |
| POST   | `/api/documents/upload`                     | Upload a document              |
| GET    | `/api/documents`                            | List user's documents (paginated)|
| GET    | `/api/documents/{id}`                       | Get document details + fields  |
| DELETE | `/api/documents/{id}`                       | Delete a document              |
| PUT    | `/api/documents/{id}/fields/{field_id}`     | Update/verify a field          |
| POST   | `/api/documents/{id}/approve`               | Approve a reviewed document    |
| GET    | `/api/dashboard/stats`                      | Get dashboard statistics       |
| GET    | `/api/dashboard/recent-documents`           | Get recent documents           |
| GET    | `/api/workflows`                            | List all workflows             |
| POST   | `/api/workflows`                            | Create a new workflow          |
| GET    | `/api/health`                               | Health check                   |

---

## 🏢 9. Relevance to Torrent Power

### How This Project Maps to Energy Sector Needs:

| DocuFlow AI Feature          | Torrent Power Use Case                                    |
|------------------------------|-----------------------------------------------------------|
| **Invoice Processing**       | Automating vendor invoice data entry for accounts payable |
| **KYC Document Handling**    | New customer connection applications, identity verification |
| **Receipt Processing**       | Payment receipt verification, customer payment reconciliation |
| **Workflow Automation**      | Auto-routing high-value invoices for approval, escalation rules |
| **Confidence-Based Review**  | Ensuring data quality — only flagging uncertain extractions |
| **Dashboard Analytics**      | Management visibility into document processing metrics    |
| **Multi-User Auth**          | Department-wise access control for finance, HR, operations |
| **Scalable Architecture**    | Handles thousands of documents during billing cycles      |

### Real-World Scenario at Torrent Power:
> A customer applies for a new electricity connection. They submit KYC documents (Aadhaar, PAN card). DocuFlow AI:
> 1. Extracts text from the scanned documents using OCR
> 2. Classifies them as KYC documents
> 3. Extracts Name, DOB, ID Number, Address
> 4. If confidence is high → auto-processes
> 5. If confidence is low → routes to an operator for verification
> 6. On approval → triggers workflow to update CRM, notify the connections team

---

## 🧪 10. How to Run the Project

### Option A: Local Development
```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Option B: Docker Compose
```bash
docker-compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

---

## 🎯 11. Key Design Decisions (Interview Talking Points)

### Q: "Why regex-based extraction instead of an ML model?"
> **A:** "I chose deterministic heuristics because they are **explainable, predictable, and don't require training data**. In an enterprise setting, you need to know *why* a field was extracted a certain way — for audit purposes. Regex rules give you that traceability. An ML model is a great next step for handling edge cases, but the rule-based system handles 90%+ of standard business documents reliably."

### Q: "Why FastAPI over Flask/Django?"
> **A:** "FastAPI provides **automatic OpenAPI documentation**, **native async support** for background tasks (document processing), **Pydantic validation** for request/response schemas, and is significantly faster than Flask. It's the modern Python standard for building APIs."

### Q: "How do you handle scanned PDFs?"
> **A:** "I have a **dual-fallback strategy**. First, I try to extract embedded text using PyMuPDF. If the PDF has no text layer (scanned document), I render each page to an image at 144 DPI and run Tesseract OCR on each page. This handles both digital and scanned PDFs without any user intervention."

### Q: "How does the confidence system work?"
> **A:** "Each extraction rule assigns a confidence score based on how reliably the pattern matches. For example, a regex match on `invoice_number` with a specific pattern gets 0.97 confidence, while a heuristic guess at a vendor name gets 0.82. Fields below 0.75 trigger human review. This **human-in-the-loop** approach ensures data quality while automating the majority of processing."

### Q: "How would you scale this for production?"
> **A:** "Three things: (1) Switch SQLite to **PostgreSQL** — just change the DATABASE_URL. (2) Add a **message queue** (Redis + Celery) for document processing instead of FastAPI's background tasks. (3) Deploy with **Docker + Kubernetes** for horizontal scaling. The architecture is already containerized and stateless."

### Q: "What's the workflow engine?"
> **A:** "It's a **rule-based automation system**. Users define rules like 'If an invoice has total_amount > ₹50,000, send an email to the finance head AND post to the Slack #approvals channel.' The engine evaluates conditions against extracted fields using comparison operators and executes the configured actions. All executions are logged with status tracking and retry counts."

---

## 📊 12. Project Metrics

| Metric                          | Value                    |
|---------------------------------|--------------------------|
| Total Backend Python files      | ~15                      |
| Total Frontend React components | ~10                      |
| Lines of code (extraction logic)| ~780 lines               |
| Supported document types        | 5 + generic fallback     |
| API endpoints                   | 13                       |
| Database tables                 | 5 (users, documents, extracted_fields, workflows, workflow_logs) |
| Auth mechanism                  | JWT with bcrypt hashing  |
| Deployment                      | Docker Compose ready     |

---

## 🚀 13. Future Enhancements

1. **LLM-Powered Extraction** — Use GPT-4o or Gemini for complex/unstructured documents
2. **Active Learning** — Feed human corrections back to improve extraction rules
3. **Batch Upload** — Process multiple documents in parallel
4. **Role-Based Access** — Admin, reviewer, uploader roles
5. **Audit Trail** — Complete history of who reviewed/approved what and when
6. **Webhook Integration** — Trigger external systems via webhooks
7. **Template Matching** — Learn document layouts from approved examples

---

*Built with ❤️ using Python (FastAPI) + React (Vite) + SQLAlchemy + Tesseract OCR*

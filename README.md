# 🛡️ Raksha+ Backend API — Project Documentation

> **AI-Powered Women Safety & Real-Time Emergency Response System (REST API)**  
> High-performance async backend powered by **FastAPI**, **MongoDB (Motor)**, **Scikit-Learn ML Threat Intelligence**, and **Geoapify Tactical Geolocation Services**.

---

## 📋 Table of Contents
1. [Architecture & System Overview](#-architecture--system-overview)
2. [Packages, Libraries & Plugins Used](#-packages-libraries--plugins-used)
3. [Project Directory Structure](#-project-directory-structure)
4. [Environment Setup & Configuration](#-environment-setup--configuration)
5. [How to Run & Access the Server](#-how-to-run--access-the-server)
6. [Interactive API Explorers (Swagger & ReDoc)](#-interactive-api-explorers)
7. [Authentication & Security Model](#-authentication--security-model)
8. [Complete API Endpoints & Slug Reference](#-complete-api-endpoints--slug-reference)
   - [1. Health & Core](#1-health--core)
   - [2. Authentication (`/api/v1/auth`)](#2-authentication-apiv1auth)
   - [3. SOS Emergency Engine (`/api/v1/sos`)](#3-sos-emergency-engine-apiv1sos)
   - [4. Emergency Contacts (`/api/v1/contacts`)](#4-emergency-contacts-apiv1contacts)
   - [5. Evidence Vault (`/api/v1/evidence`)](#5-evidence-vault-apiv1evidence)
   - [6. AI Threat Intelligence (`/api/v1/threat`)](#6-ai-threat-intelligence-apiv1threat)
   - [7. Maps & Location Services (`/api/v1/places`)](#7-maps--location-services-apiv1places)
   - [8. Incident Logs & History (`/api/v1/incidents`)](#8-incident-logs--history-apiv1incidents)
   - [9. Admin Command & Dispatch Center (`/api/v1/admin`)](#9-admin-command--dispatch-center-apiv1admin)
   - [10. Static Media Storage (`/uploads`)](#10-static-media-storage-uploads)
9. [AI Threat Classifier Pipeline](#-ai-threat-classifier-pipeline)
10. [Database Indexes & Performance](#-database-indexes--performance)
11. [Deployment Guide](#-deployment-guide)

---

## 🏛️ Architecture & System Overview

Raksha+ Backend serves as the secure mission-control backend interconnecting:
- **`raksha_client`**: Flutter Android & iOS mobile safety app for citizens and women commuters.
- **`Raksha-Admin`**: Next.js 16 command & police dispatch center for law enforcement and emergency response coordinators.
- **External Services**: Resend Email API, Geoapify Geocoding & Routing, Cloudinary Media Vault, and OpenStreetMap.

```
       ┌────────────────────────┐         ┌────────────────────────┐
       │   Raksha Mobile App    │         │      Raksha Admin      │
       │   (Flutter iOS/Android)│         │     (Next.js 16 App)   │
       └───────────┬────────────┘         └───────────┬────────────┘
                   │                                  │
                   ▼                                  ▼
      ═══════════════════════════════════════════════════════════════
                 FastAPI Backend Engine (Uvicorn / ASGI)
      ═══════════════════════════════════════════════════════════════
        ├── JWT Auth (365-Day Long-Lived Tokens + Bcrypt Hashes)
        ├── SOS Live Location Broadcaster & Polyline GPS Engine
        ├── Ambient Microphone Audio Streaming & Multipart Uploads
        ├── Anti-Theft Stealth Beacons & Fake Shutdown Defense
        ├── AI Threat Inference Engine (Scikit-Learn Classifier)
        ├── Geoapify Reverse Geocoder & Proximity Danger Radar
        └── Police Dispatch Docket & Real-Time Tracking Registry
                   │                                  │
                   ▼                                  ▼
      ┌────────────────────────┐         ┌────────────────────────┐
      │  MongoDB Atlas Cluster │         │ Static / Cloud Storage │
      │  (Async Motor Driver)  │         │ (Local Disk / Cloudinary)│
      └────────────────────────┘         └────────────────────────┘
```

---

## 📦 Packages, Libraries & Plugins Used

All dependencies are defined in `requirements.txt`:

| Package / Library | Version | Category | Purpose in Raksha+ |
|---|---|---|---|
| **`fastapi`** | `0.115.6` | Web Framework | Modern, high-speed ASGI web framework with automatic OpenAPI/Swagger docs and strict validation. |
| **`uvicorn[standard]`** | `0.34.0` | ASGI Server | High-concurrency production ASGI web server powering FastAPI with uvloop & httptools. |
| **`motor`** | `3.6.0` | Database Driver | Asynchronous MongoDB Python driver enabling non-blocking database queries with coroutines. |
| **`pymongo`** | `4.9.2` | Database Toolkit | Core MongoDB toolkit providing geospatial 2dsphere indexing and BSON ObjectId operations. |
| **`pydantic`** | `>=2.11.0` | Data Validation | Strict data validation, type enforcement, schema definitions, and JSON serialization. |
| **`pydantic-settings`** | `>=2.8.0` | Config Management | Type-safe environment variable parsing from `.env` with auto-casting and validation. |
| **`python-jose[cryptography]`** | `3.3.0` | Security & Auth | Encodes and validates JSON Web Tokens (JWT) with HMAC-SHA256 signatures for citizen & admin auth. |
| **`passlib[bcrypt]`** & **`bcrypt`** | `1.7.4` / `4.0.1` | Cryptography | Secure password salting and hashing preventing plain-text credential leaks. |
| **`python-multipart`** | `0.0.20` | File Streaming | Multipart form-data streaming parser for direct audio, video, and photo evidence uploads. |
| **`cloudinary`** | `1.41.0` | Cloud Media | Cloud media asset management and signed URL generation for encrypted off-site evidence storage. |
| **`httpx`** | `0.28.1` | HTTP Client | Async HTTP client for outbound API requests (Resend Email alerts, Geoapify IP & address lookups). |
| **`scikit-learn`** | `>=1.8.0` | Machine Learning | Machine learning framework executing the Random Forest threat classifier. |
| **`numpy`** | `>=2.3.3` | Math & Arrays | Numerical computing library handling input feature vectors for ML model inference. |
| **`joblib`** | `1.4.2` | Model Persistence | Serializes and loads pre-trained scikit-learn models (`.joblib` format) at server startup. |
| **`slowapi`** | `>=0.1.9` | Rate Limiting | In-memory token bucket rate limiter protecting login, SOS trigger, and refresh endpoints. |
| **`email-validator`** | `2.2.0` | Validation | Validates email syntax and deliverability format across auth and contact routers. |
| **`python-dotenv`** | `1.0.1` | Environment | Loads `.env` file variables into `os.environ` during development. |
| **`pytest`** & **`pytest-asyncio`** | `>=8.0.0` | Unit Testing | Test runner for executing asynchronous endpoint integration tests. |
| **`mongomock-motor`** | `>=0.0.35` | Testing Mock | In-memory mock MongoDB engine allowing unit tests to run without an active MongoDB connection. |

---

## 📂 Project Directory Structure

```
raksha-backend/
├── app/
│   ├── main.py                       # FastAPI application setup, CORS, static mounts, router injection
│   ├── deps.py                       # Dependency injection (get_current_user, require_admin, DB guards)
│   ├── core/
│   │   ├── config.py                 # Pydantic Settings class loading .env variables
│   │   ├── database.py               # Async Motor MongoDB connection, collections, and 2dsphere indexes
│   │   ├── security.py               # Password hashing (Bcrypt) and JWT token generation / decoding
│   │   └── limiter.py                # SlowAPI rate limiter instance
│   ├── models/                       # Pydantic Request & Response data models
│   │   ├── user.py                   # User schemas, token pairs, profile updates
│   │   ├── contact.py                # Emergency contact schema
│   │   ├── incident.py               # SOS incident, location logs, evidence metadata
│   │   ├── threat.py                 # AI threat inference input/output schemas
│   │   └── admin.py                  # Danger zones, police dispatch, audit logs
│   ├── routers/                      # Modular API Controllers (M1 - M8)
│   │   ├── auth.py                   # Register, login, 365-day token refresh, user profile
│   │   ├── sos.py                    # SOS trigger, live tracking, audio upload, guardian tracking, emails
│   │   ├── contacts.py               # Trusted safety circle CRUD
│   │   ├── evidence.py               # Cloudinary signature, evidence registration & listing
│   │   ├── threat.py                 # AI threat assessment & decibel loudness analyzer
│   │   ├── places.py                 # Nearby police/hospitals, reverse geocoding, danger zones
│   │   ├── incidents.py              # User incident history & location trail queries
│   │   └── admin.py                  # Complete admin suite (dispatch, users, danger zones, reports)
│   └── services/                     # Business Logic Services
│       ├── threat_detector.py        # ML Random Forest classifier pipeline
│       ├── maps_service.py           # Geoapify API integrations (reverse geocoding, places)
│       ├── notification_service.py   # Resend emergency email dispatcher & SMS alerts
│       ├── audit_service.py          # Security and dispatch audit logging
│       └── cloudinary_service.py     # Signed upload parameter generation
├── uploads/                          # Local storage directory for direct multipart evidence
│   └── audio/                        # Captured SOS ambient microphone .m4a recordings
├── main.py                           # Root runner script for Uvicorn
├── train_model.py                    # Training script for AI threat detection model
├── requirements.txt                  # Python dependencies
├── .env                              # Environment configuration (Private, git-ignored)
└── README.md                         # This comprehensive project documentation
```

---

## ⚙️ Environment Setup & Configuration

Create a `.env` file in the `raksha-backend/` root directory:

```env
# ── Application Settings ──
APP_NAME="Raksha+ Safety API"
DEBUG=true
API_V1_PREFIX="/api/v1"

# ── Security & JWT Authentication ──
# Generate a secret: python -c "import secrets; print(secrets.token_urlsafe(64))"
JWT_SECRET_KEY="super_secret_64_character_random_hash_key_for_raksha_plus"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=525600      # 365 Days login persistence
REFRESH_TOKEN_EXPIRE_DAYS=365           # 365 Days refresh token lifetime

# ── MongoDB Connection ──
MONGODB_URI="mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority"
MONGODB_DB_NAME="raksha_plus_db"

# ── External Maps & Geolocation ──
GEOAPIFY_API_KEY_GEOLOCATOR="your_geoapify_api_key_here"
GOOGLE_MAPS_API_KEY=""                 # Optional fallback

# ── Email Alerts (Resend) ──
RESEND_API_KEY="re_xxxxxxxxxxxxxxxxxxxx"
ALERT_FROM_EMAIL="alerts@resend.dev"

# ── Cloud Media Evidence (Cloudinary) ──
CLOUDINARY_CLOUD_NAME="your_cloud_name"
CLOUDINARY_API_KEY="your_cloudinary_api_key"
CLOUDINARY_API_SECRET="your_cloudinary_secret"

# ── CORS Settings ──
CORS_ORIGINS="http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000"
```

---

## 🚀 How to Run & Access the Server

### 1. Prerequisites
- Python **3.11** or **3.12** installed
- MongoDB instance (MongoDB Atlas free M0 cluster or local MongoDB)

### 2. Setup Virtual Environment
```bash
# Navigate to backend folder
cd "e:/Raksha Plus/raksha-backend"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
.\venv\Scripts\activate.bat
# Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. (Optional) Train the AI Threat Classifier
```bash
python train_model.py
```
*Generates `app/services/models/threat_classifier.joblib` containing the trained Random Forest classifier.*

### 4. Start the Server
```bash
# Method 1: Using Uvicorn direct reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Method 2: Running the main.py entrypoint
python main.py
```

---

## 🔍 Interactive API Explorers

Once the server is running, explore and test all endpoints interactively:

- **Swagger UI (Interactive API Tester)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc (Clean API Specification)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Schema (JSON Format)**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 🔐 Authentication & Security Model

Raksha+ uses **Bearer Token Authentication** (`Authorization: Bearer <access_token>`).

- **Token Lifetime**: 365 Days (`525,600` minutes). Eliminates annoying daily logouts while maintaining cryptographic security.
- **Refresh Flow**: When refreshing tokens, send `{ "refresh_token": "..." }` to `POST /api/v1/auth/refresh`.
- **Protected Routes**: Any endpoint requiring authentication must receive the Bearer token in the request header:
  ```http
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  ```
- **Admin Endpoints**: Require users with the role `ADMIN` or the dedicated admin token from `/api/v1/admin/login`.

---

## 📑 Complete API Endpoints & Slug Reference

### 1. Health & Core

| Method | Endpoint Slug | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | Public | Server liveness check and database status |

#### `GET /health`
- **Response `200 OK`**:
  ```json
  {
    "status": "ok",
    "app": "Raksha+ Safety API"
  }
  ```

---

### 2. Authentication (`/api/v1/auth`)

| Method | Endpoint Slug | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Public | Register a new user account with phone & email |
| `POST` | `/api/v1/auth/login` | Public | Authenticate user credentials & receive token pair |
| `POST` | `/api/v1/auth/refresh` | Public | Refresh expired access token using refresh token |
| `GET` | `/api/v1/auth/me` | Bearer | Retrieve current authenticated user profile |
| `PATCH` | `/api/v1/auth/me` | Bearer | Update user profile, medical info, and emergency notes |

#### `POST /api/v1/auth/register`
- **Request Body**:
  ```json
  {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "+919876543210",
    "password": "SecurePassword@123",
    "phone_imei": "867459038291045",
    "blood_group": "B+",
    "medical_notes": "Asthmatic, carries inhaler",
    "home_address": "42 Green Valley, Sector 14, Gurugram"
  }
  ```
- **Response `201 Created`**: Returns `UserOut` model without password hash.

#### `POST /api/v1/auth/login`
- **Request Body**:
  ```json
  {
    "email": "jane@example.com",
    "password": "SecurePassword@123"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in": 31536000
  }
  ```

#### `POST /api/v1/auth/refresh`
- **Request Body**:
  ```json
  {
    "refresh_token": "eyJhbGciOi..."
  }
  ```
- **Response `200 OK`**: Returns a new `TokenPair` valid for another 365 days.

---

### 3. SOS Emergency Engine (`/api/v1/sos`)

| Method | Endpoint Slug | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/sos/trigger` | Bearer | Instant emergency trigger. Creates active incident, dispatches alerts. |
| `POST` | `/api/v1/sos/{incident_id}/location` | Bearer | Stream high-frequency live GPS breadcrumbs during active SOS. |
| `POST` | `/api/v1/sos/{incident_id}/stop` | Bearer | Cancel / resolve the active emergency incident. |
| `GET` | `/api/v1/sos/active` | Bearer | Fetch the user's currently live SOS incident (if active). |
| `POST` | `/api/v1/sos/{incident_id}/audio` | Bearer | Link an emergency audio stream URL to the incident. |
| `POST` | `/api/v1/sos/{incident_id}/upload-audio` | Bearer | **Multipart Upload**: Upload raw ambient microphone `.m4a` audio file. |
| `GET` | `/api/v1/sos/track/{target_id}` | Public | **Guardian QR Tracking**: Scans user or incident ID to track live GPS. |
| `POST` | `/api/v1/sos/{incident_id}/send-email` | Bearer | Automatically send live location email with map link via Resend. |

#### `POST /api/v1/sos/trigger`
- **Request Body**:
  ```json
  {
    "location": {
      "lat": 28.4715,
      "lng": 77.0725
    },
    "trigger_type": "manual"
  }
  ```
- **Response `201 Created`**:
  ```json
  {
    "incident_id": "6718a2bc4f3d2a1b9c8e7f6a",
    "status": "ACTIVE",
    "triggered_at": "2026-10-22T22:30:00Z",
    "location": {
      "lat": 28.4715,
      "lng": 77.0725
    }
  }
  ```

#### `POST /api/v1/sos/{incident_id}/upload-audio`
- **Content-Type**: `multipart/form-data`
- **Form Data**:
  - `file`: `[Binary .m4a / .wav / .mp3 audio file]`
- **Response `200 OK`**:
  ```json
  {
    "status": "ok",
    "audio_url": "/uploads/audio/sos_6718a2bc_a1b2c3d4.m4a"
  }
  ```

#### `GET /api/v1/sos/track/{target_id}`
- **Parameters**: `target_id` = Target User's MongoDB ID or Active Incident ID.
- **Response `200 OK`**: Returns target user name, phone, emergency status, live coordinates, and latest audio link.

---

### 4. Emergency Contacts (`/api/v1/contacts`)

| Method | Endpoint Slug | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/contacts` | Bearer | List all safety circle contacts for the current user |
| `POST` | `/api/v1/contacts` | Bearer | Add a new emergency contact (parent, friend, spouse) |
| `PUT` | `/api/v1/contacts/{contact_id}` | Bearer | Update contact details, phone, or notification priority |
| `DELETE` | `/api/v1/contacts/{contact_id}` | Bearer | Remove contact from emergency circle |

#### `POST /api/v1/contacts`
- **Request Body**:
  ```json
  {
    "name": "Mom",
    "phone": "+919811223344",
    "relationship": "Mother",
    "email": "mom@family.com",
    "notify_by_sms": true,
    "notify_by_email": true
  }
  ```

---

### 5. Evidence Vault (`/api/v1/evidence`)

| Method | Endpoint Slug | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/evidence/upload-signature` | Bearer | Request signed params to upload directly to Cloudinary |
| `POST` | `/api/v1/evidence` | Bearer | Register uploaded evidence (Audio/Video/Photo) with an incident |
| `GET` | `/api/v1/evidence/{incident_id}` | Bearer | Fetch all recorded evidence items attached to an incident |

#### `POST /api/v1/evidence`
- **Request Body**:
  ```json
  {
    "incident_id": "6718a2bc4f3d2a1b9c8e7f6a",
    "type": "AUDIO",
    "cloudinary_url": "https://res.cloudinary.com/.../evidence_audio.m4a",
    "duration": 22.5,
    "size_kb": 480.0
  }
  ```

---

### 6. AI Threat Intelligence (`/api/v1/threat`)

| Method | Endpoint Slug | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/threat/evaluate` | Bearer | Multi-sensor evaluation: motion speed, audio dB, dark zone factor |
| `POST` | `/api/v1/threat/decibel` | Bearer | Submit microphone loudness readings to detect sudden screams |
| `GET` | `/api/v1/threat/status` | Bearer | Check the current AI threat engine operational status |

#### `POST /api/v1/threat/evaluate`
- **Request Body**:
  ```json
  {
    "speed_mps": 0.2,
    "accel_magnitude": 14.8,
    "decibel_level": 88.5,
    "is_dark_area": true,
    "time_of_day_hour": 23
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "threat_level": "HIGH",
    "confidence_score": 0.94,
    "should_auto_trigger_sos": true,
    "threat_indicators": [
      "Sudden high decibel spike (possible scream)",
      "High acceleration jerk motion detected",
      "Commuting late night in high-risk isolated zone"
    ]
  }
  ```

---

### 7. Maps & Location Services (`/api/v1/places`)

| Method | Endpoint Slug | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/places/nearby` | Bearer | Find nearest Police Stations and Emergency Hospitals |
| `GET` | `/api/v1/places/reverse-geocode` | Bearer | Convert GPS coordinates into human-readable street address |
| `GET` | `/api/v1/places/ip-location` | Bearer | Approximate client location from IP when GPS is unavailable |
| `GET` | `/api/v1/places/danger-zones` | Bearer | **Real-Time Danger Zones**: Active circles & road corridor lines |

#### `GET /api/v1/places/danger-zones`
- **Response `200 OK`**:
  ```json
  [
    {
      "id": "6718b5de9f2e1a3b8c7d6e5f",
      "title": "Unlit Canal Road (Late Night)",
      "description": "Broken streetlights, zero pedestrian traffic after 9 PM.",
      "zone_type": "ROAD_LINE",
      "latitude": 28.4715,
      "longitude": 77.0725,
      "radius_m": 100,
      "path_coordinates": [
        [28.47150, 77.07250],
        [28.47210, 77.07340],
        [28.47350, 77.07510]
      ],
      "severity": "HIGH",
      "is_active": true
    },
    {
      "id": "6718c1ab3f4d5e6a7b8c9d0e",
      "title": "Dark Underpass - Low Visibility",
      "description": "Cautionary area.",
      "zone_type": "CIRCLE",
      "latitude": 28.4894,
      "longitude": 77.0898,
      "radius_m": 350,
      "path_coordinates": [],
      "severity": "MODERATE",
      "is_active": true
    }
  ]
  ```

---

### 8. Incident Logs & History (`/api/v1/incidents`)

| Method | Endpoint Slug | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/incidents` | Bearer | Retrieve paginated history of past SOS incidents for user |
| `GET` | `/api/v1/incidents/{incident_id}` | Bearer | Get full incident dossier including duration and evidence |
| `GET` | `/api/v1/incidents/{incident_id}/logs` | Bearer | Fetch complete GPS breadcrumb trail logs of the incident |

---

### 9. Admin Command & Dispatch Center (`/api/v1/admin`)

| Method | Endpoint Slug | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/admin/login` | Public | Authenticate Raksha Admin credentials (`admin` / `Admin@123`) |
| `GET` | `/api/v1/admin/overview` | Admin | High-level metrics: Active SOS, total users, threats, dispatches |
| `GET` | `/api/v1/admin/users` | Admin | Directory of all registered users with IMEI & medical notes |
| `GET` | `/api/v1/admin/users/{user_id}` | Admin | Detailed dossier of a single user |
| `GET` | `/api/v1/admin/incidents` | Admin | Complete incident feed with filters (Active, Resolved, False) |
| `GET` | `/api/v1/admin/evidence` | Admin | Master evidence vault (all recorded audio, video, and photos) |
| `GET` | `/api/v1/admin/reports` | Admin | Citizen safety reports, harassment complaints, queries |
| `PATCH`| `/api/v1/admin/reports/{report_id}` | Admin | Update status of citizen report (`INVESTIGATING`, `RESOLVED`) |
| `GET` | `/api/v1/admin/live-tracking` | Admin | Real-time map telemetry for all live emergency users |
| `POST` | `/api/v1/admin/dispatch-police` | Admin | **Police Dispatch**: Transmits live GPS, IMEI & docket to police |
| `GET` | `/api/v1/admin/dispatch-history`| Admin | History of all police and PCR patrol van dispatches |
| `GET` | `/api/v1/admin/danger-zones` | Admin | List all marked danger zones & road hazard corridors |
| `POST` | `/api/v1/admin/danger-zones` | Admin | **Mark Danger Zone**: Create a Circle Area or Road Line Corridor |
| `PATCH`| `/api/v1/admin/danger-zones/{zone_id}`| Admin| Update zone status (`is_active: false`) or radius |
| `DELETE`| `/api/v1/admin/danger-zones/{zone_id}`| Admin| Permanently remove danger zone from mobile broadcast |
| `PUT` | `/api/v1/admin/credentials` | Admin | Change admin login username and password |

#### `POST /api/v1/admin/danger-zones` (Road Corridor vs Circle)
- **Marking a Road / Line Corridor**:
  ```json
  {
    "title": "Unlit Highway Connector",
    "description": "Zero streetlights, frequent harassment reports.",
    "severity": "HIGH",
    "zone_type": "ROAD_LINE",
    "latitude": 28.4715,
    "longitude": 77.0725,
    "radius_m": 100,
    "path_coordinates": [
      [28.47150, 77.07250],
      [28.47210, 77.07340],
      [28.47350, 77.07510]
    ],
    "is_active": true
  }
  ```

#### `POST /api/v1/admin/dispatch-police`
- **Request Body**:
  ```json
  {
    "incident_id": "6718a2bc4f3d2a1b9c8e7f6a",
    "user_id": "671891af1c2b3d4e5f6a7b8c",
    "police_station": "DLF Phase 2 Police Station",
    "police_phone": "112",
    "priority": "IMMEDIATE_LIFE_THREAT",
    "officer_notes": "Victim surrounded by suspicious group. Audio confirms distress call."
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "status": "DISPATCHED",
    "docket_number": "POLICE-DISPATCH-948201",
    "dispatched_at": "2026-10-22T22:35:10Z",
    "transmitted_payload": {
      "victim_name": "Jane Doe",
      "phone": "+919876543210",
      "imei": "867459038291045",
      "coordinates": { "lat": 28.4715, "lng": 77.0725 },
      "live_map_url": "https://maps.google.com/?q=28.4715,77.0725",
      "audio_evidence_url": "/uploads/audio/sos_6718a2bc.m4a"
    }
  }
  ```

---

### 10. Static Media Storage (`/uploads`)

Direct evidence files uploaded by the mobile client during emergency triggers are stored on disk and served statically:

- **Audio URL**: `GET http://localhost:8000/uploads/audio/{filename}`
- Example: `http://localhost:8000/uploads/audio/sos_6718a2bc_a1b2c3d4.m4a`

---

## 🧠 AI Threat Classifier Pipeline

Located in `app/services/threat_detector.py`:
- **Model**: `RandomForestClassifier` trained via `train_model.py`.
- **Features Vector**:
  1. `speed_mps`: User travel speed (detects sudden stops or forced running).
  2. `accel_magnitude`: Phone accelerometer jerk / struggle detection.
  3. `decibel_level`: Microphone volume level (screams, sirens, sudden shouts).
  4. `is_dark_area`: Binary indicator if user is located in an unlit/hazardous zone.
  5. `hour_of_day`: Circadian danger factor (late night 23:00–04:00 weight).
- **Auto-Trigger Threshold**: Confidence score `>= 0.85` triggers automatic SOS dispatch to safety circle and police.

---

## 🗄️ Database Indexes & Performance

Configured automatically on server boot via `create_indexes()` in `app/core/database.py`:

```python
# Geospatial 2dsphere indexes for rapid proximity searches
await incidents_collection().create_index([("location", "2dsphere")])
await location_logs_collection().create_index([("coordinates", "2dsphere")])

# Fast compound lookup indexes
await users_collection().create_index("email", unique=True)
await users_collection().create_index("phone", unique=True)
await location_logs_collection().create_index([("incident_id", 1), ("timestamp", -1)])
await danger_zones_collection().create_index([("is_active", 1)])
```

---

## 🌐 Deployment Guide

### Deploying to Render / Railway / AWS EC2

1. **Production Command**:
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:$PORT
   ```
2. **Environment Variables**:
   In your hosting dashboard (e.g., Render, Railway), set all variables from `.env`:
   - `JWT_SECRET_KEY`
   - `MONGODB_URI`
   - `GEOAPIFY_API_KEY_GEOLOCATOR`
   - `RESEND_API_KEY`
   - `CLOUDINARY_*`
3. **Persisting Uploads**: Mount a persistent storage volume to `/uploads` so that recorded audio evidence files survive container redeployments.

---

*Raksha+ Backend is engineered for mission-critical reliability, rapid emergency dispatch, and uninterrupted women safety surveillance.*

# Raksha+ Backend

FastAPI backend for **Raksha+: AI-Powered Women Safety and Emergency
Response System** (MCSP-232). Implements modules M1–M8 from the project
synopsis: Auth, SOS Engine, Location Tracker, Evidence Capture, AI Threat
Detector, Map & Places, Incident History, and Admin.

## 1. Set up the virtual environment

```bash
# from the raksha-backend/ folder
python3 -m venv venv

# activate it
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows (cmd/powershell)

# install dependencies
pip install -r requirements.txt
```

You'll know it worked if your terminal prompt shows `(venv)` at the start.
Deactivate anytime with `deactivate`.

## 2. Configure environment variables

Copy the example file and fill in real values — **never commit `.env`**,
it's already listed in `.gitignore`.

```bash
cp .env.example .env
```

Then edit `.env`:

| Variable | Where to get it |
|---|---|
| `JWT_SECRET_KEY` | Generate: `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `MONGODB_URI` | MongoDB Atlas → free M0 cluster → "Connect" → driver connection string |
| `CLOUDINARY_*` | Cloudinary dashboard → free tier → API keys |
| `GOOGLE_MAPS_API_KEY` | Google Cloud Console → enable Places API + Maps SDK |

## 3. (Optional) Train the basic threat classifier

```bash
python train_model.py
```

This creates `app/services/models/threat_classifier.joblib` from synthetic
data — good enough to demo M5 end-to-end. Swap in real labeled data later
without touching any router code.

## 4. Run the server

```bash
uvicorn app.main:app --reload
```

- API docs (Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Project structure

```
app/
├── main.py              # FastAPI app + router wiring
├── deps.py               # get_current_user, require_admin (JWT + RBAC)
├── core/
│   ├── config.py         # reads .env via pydantic-settings
│   ├── database.py       # Motor async MongoDB client
│   └── security.py       # bcrypt hashing, JWT create/decode
├── models/                # Pydantic request/response schemas
├── routers/               # one file per module (M1-M8)
└── services/              # Cloudinary, Google Maps, threat detector, notifications
```

## Deploying free

Render or Railway free web service + MongoDB Atlas M0 + Cloudinary free
tier + Google Maps $200/month credit — all $0 for an academic build.
Set the same variables from `.env` in your host's environment variable
dashboard (never upload the `.env` file itself).

# Fruit-CBIR Project

## What This Is
A university group project (3 members) building a **Content-Based Image Retrieval** system for fruit images. Upload a fruit photo, get the 5 most visually similar images from the database.

## Tech Stack
- **Frontend**: React 18 + Vite + Tailwind CSS + react-dropzone + Chart.js
- **Backend**: Flask 3.x REST API (port 5001)
- **Database**: PostgreSQL 16 via Docker
- **Data**: 7,147 preprocessed fruit images (224x224 PNG, background removed)

## Quick Start

```bash
# 1. Start PostgreSQL
docker compose up -d

# 2. Start backend (terminal 1)
cd backend
source .venv/bin/activate
python run.py
# -> http://localhost:5001

# 3. Start frontend (terminal 2)
cd frontend
npm run dev
# -> http://localhost:5173
```

Note: Flask runs on port **5001** (not 5000 — macOS AirPlay uses 5000).

## Project Structure

```
Fruit-CBIR/
├── docker-compose.yml                 # PostgreSQL 16
├── Fruits_data_processed/             # 7,147 images, 8 categories
│   ├── Apples_processed/     (911)
│   ├── Bananas_processed/    (1,408)
│   ├── Grapes_processed/     (1,295)
│   ├── Mangoes_processed/    (1,368)
│   ├── Oranges_processed/    (1,358)
│   ├── Peaches_processed/    (248)
│   ├── Pomegranates_processed/ (310)
│   └── Strawberries_processed/ (249)
│
├── backend/
│   ├── app/
│   │   ├── __init__.py                # Flask factory + CORS
│   │   ├── config.py                  # Loads from .env
│   │   └── api/
│   │       ├── routes.py              # Endpoints (see below)
│   │       └── search_interface.py    # *** INTEGRATION POINT for Member B ***
│   ├── database/
│   │   ├── schema.sql                 # 3 tables: images, features, query_logs
│   │   └── db_manager.py             # PostgreSQL CRUD
│   ├── scripts/
│   │   └── index_dataset.py          # Batch index images into DB
│   └── .env                           # DATABASE_URL
│
├── frontend/
│   ├── src/
│   │   ├── pages/HomePage.jsx         # Upload page (drag-drop)
│   │   ├── pages/ResultPage.jsx       # Top-5 results + charts
│   │   ├── components/ImageUpload.jsx
│   │   ├── components/ResultGrid.jsx
│   │   ├── components/FeatureCharts.jsx
│   │   └── services/api.js           # Axios calls to backend
│   └── vite.config.js                 # Proxy /api -> localhost:5001
│
├── evaluation/
│   ├── build_ground_truth.py          # Generates ground_truth.json
│   ├── ground_truth.json              # 29 queries (3-4 per category)
│   └── evaluate_fruit.py             # Computes P@5, mAP
│
├── rembg_module_preprocess.py         # Original preprocessing script (Member A)
├── ke_hoach_bai_tap_lon_CBIR.md       # Full project plan (Vietnamese)
└── timeline.md                        # 4-week timeline
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload query image -> save -> insert DB -> returns `{image_id}` |
| GET | `/api/search?image_id=<id>` | Returns top-5 similar images (currently mock/random) |
| GET | `/api/images/<id>` | Single image metadata |
| GET | `/api/stats` | DB stats: total images, per-category counts |
| GET | `/api/dataset/<path>` | Serves images from Fruits_data_processed/ |

## Database (PostgreSQL)

3 tables in `fruit_cbir` database:
- **images** — 7,147 rows (filename, filepath, fruit_label, dimensions)
- **features** — empty (waiting for Member B's feature extraction)
- **query_logs** — search query history

Connection: `postgresql://cbir_user:cbir_pass@localhost:5432/fruit_cbir`

## Team Responsibilities

### Member A — Data & Preprocessing (DONE)
- [x] 7,147 images collected and preprocessed (224x224 PNG, rembg)
- [x] Batch indexed into PostgreSQL
- [x] Ground truth: 29 queries in evaluation/ground_truth.json
- [x] Evaluation script: evaluate_fruit.py (P@5, mAP)
- [ ] Write report sections (data + evaluation)

### Member B — Features & Search Algorithm (NOT STARTED)
Only file to modify: `backend/app/api/search_interface.py`

Two functions to implement:
1. `extract_features(image_id, filepath)` — extract feature vectors, store in DB
2. `search_similar(image_id, top_k)` — find top-k nearest neighbors

Features to implement (from pochih/CBIR + custom):
- Color Histogram, Gabor, Edge, HOG (adapt from pochih)
- Color Moments, Hu Moments, GLCM, LBP (write new)
- Weighted fusion + KD-Tree/FAISS index

After implementing, re-index: `cd backend && python scripts/index_dataset.py --clear`

### Member C — Web & Database (DONE)
- [x] Flask backend with REST API
- [x] React frontend (upload, results, charts)
- [x] PostgreSQL via Docker
- [x] Dataset serving route
- [ ] Polish UI, write report sections

## Useful Commands

```bash
# Re-index all images (clear + fresh index)
cd backend && source .venv/bin/activate
python scripts/index_dataset.py --clear

# Regenerate ground truth
python evaluation/build_ground_truth.py

# Run evaluation (direct mode, no server needed)
python evaluation/evaluate_fruit.py

# Run evaluation via API (server must be running)
python evaluation/evaluate_fruit.py --mode api

# Check DB stats
curl localhost:5001/api/stats
```

## Current Baseline
With mock/random search: **P@5 = 10.3%, mAP = 19.2%** (expected ~12.5% = 1/8 random).
Target after Member B implements features: **P@5 >= 70%**.

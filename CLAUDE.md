# Fruit-CBIR Project

## What This Is
University group project (3 members) — **Content-Based Image Retrieval** for fruit images. Upload a fruit photo, get top-5 visually similar images.

## Architecture
**Clean Architecture** with 4 layers:
- `domain/` — interfaces (IUseCase, IFeatureExtractor, ISearchImage, IRemoveBackground), DTOs, models
- `infrastructure/` — PostgreSQL repositories, database pool, AI models, Alembic migrations, seed data
- `usecases/` — business logic: `feature_extractor.py`, `search_images.py`, `remove_background.py`
- `presentation/` — Flask Blueprint with HTTP endpoints
- `view/` — React 18 + Vite + Tailwind frontend

## Tech Stack
- **Frontend**: React 18 + Vite + Tailwind + react-dropzone + Chart.js (port 5173)
- **Backend**: Flask 3 + Flask-SQLAlchemy + Flask-Migrate + psycopg2 (port 5001)
- **Database**: PostgreSQL 16 + **pgvector** extension via Docker
- **AI**: OpenCV + scikit-image (LBP) + rembg (background removal)
- **Python**: 3.11 (3.13 has llvmlite issues with rembg)
- **Data**: 7,147 preprocessed fruit images (224×224 PNG, RGBA, 8 categories)

Note: macOS AirPlay uses port 5000 → Flask uses **5001**.

## Quick Start

```bash
# 1. Start PostgreSQL with pgvector
docker compose up -d
docker compose exec db psql -U cbir_user -d fruit_cbir -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 2. Setup Python env (use 3.11)
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install --only-binary=:all: llvmlite numba pymatting tqdm
pip install rembg --no-deps  # avoid llvmlite build issues

# 3. Apply DB migrations
export FLASK_APP=app.py
flask db upgrade

# 4. Seed data + extract features (one-time, ~10-15 min)
python app.py reset

# 5. Run server
python app.py skip
# -> http://localhost:5001

# 6. Run frontend (separate terminal)
cd view && npm install && npm run dev
# -> http://localhost:5173
```

## Project Structure

```
Fruit-CBIR/
├── docker-compose.yml             # PostgreSQL 16 + pgvector
├── requirements.txt
├── .env                           # DB credentials, FRONTEND_URL, BACKEND_PORT
├── .env.example
├── app.py                         # Flask entry point
│
├── domain/                        # Interfaces (Clean Architecture)
│   ├── usecase.py                 # IFeatureExtractor, ISearchImage, IRemoveBackground
│   ├── repositories.py            # IFruitRepository, IImageRepository, IFeatureRepository
│   ├── dtos.py                    # SearchResult dataclass
│   ├── models.py                  # Fruit, Image, Feature
│   └── constants.py               # API paths, limits
│
├── usecases/                      # Business logic (Member B's main work)
│   ├── feature_extractor.py       # Color HSV + LBP + Hu Moments
│   ├── search_images.py           # Orchestrates extract + search
│   └── remove_background.py       # rembg wrapper
│
├── infrastructure/                # External integrations
│   ├── database/database.py       # psycopg2 connection pool
│   ├── persistence/
│   │   ├── models.py              # SQLAlchemy: FruitTable, ImageTable, FeatureTable (with pgvector)
│   │   ├── seed_data.py           # Batch seed with --reset/--clear/--skip
│   │   └── migrations/            # Alembic
│   ├── repositories/repository.py # PostgreSQL CRUD + pgvector cosine search
│   └── AI_models/
│       ├── preprocessing/rembg_module_preprocess.py  # Original preprocessing (Member A)
│       └── evaluation/            # P@5, mAP evaluation
│           ├── build_ground_truth.py
│           ├── ground_truth.json   # 29 queries
│           └── evaluate_fruit.py   # Evaluation script
│
├── presentation/controllers.py    # Flask routes (api_bp)
│
├── view/                           # React frontend
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/HomePage.jsx     # Upload + fruit gallery
│   │   ├── pages/ResultPage.jsx   # Top-5 + charts
│   │   ├── components/ImageUpload.jsx  # Drag-drop + weight tuning
│   │   ├── components/ResultGrid.jsx
│   │   └── components/FeatureCharts.jsx
│   └── package.json
│
└── static/Fruits_data_processed/  # 7,147 images, 8 categories
    ├── Apples_processed/    (911)
    ├── Bananas_processed/   (1,408)
    ├── Grapes_processed/    (1,295)
    ├── Mangoes_processed/   (1,368)
    ├── Oranges_processed/   (1,358)
    ├── Peaches_processed/   (248)
    ├── Pomegranates_processed/ (310)
    └── Strawberries_processed/ (249)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/search` | Upload image (multipart) + weights → top-5 results |
| GET | `/api/fruits` | List 8 fruit categories with sample image |
| GET | `/api/static/images/<path>` | Serve image from `static/Fruits_data_processed/` |

### Search request body (multipart):
- `image`: file (PNG/JPG)
- `top_k`: int (default 5)
- `weight_color`: float (default 0.7)
- `weight_texture`: float (default 0.2)
- `weight_shape`: float (default 0.1)

## Feature Extraction (Member B)

| Type | Method | Dim | File |
|------|--------|-----|------|
| Color | HSV histogram (16×4×4), normalize L2, mask removes white/black bg | 256 | `usecases/feature_extractor.py::_build_color_vector` |
| Texture | LBP uniform (P=8, R=1), normalize L1 | 10 | `_build_texture_vector` |
| Shape | Hu Moments (log-transformed) | 7 | `_build_shape_vector` |

Search: weighted sum of cosine distances via **pgvector** `<=>` operator.

## Database Schema

```
fruits (fruit_id PK, name, description)
images (image_id PK, fruit_id FK, filename, filepath)
features (feature_id PK, image_id FK, color VECTOR(256), texture VECTOR(10), shape VECTOR(7))
```

## Evaluation Results (2026-04-25)

```
Mean P@5:      0.8621  (target ≥ 0.70)
mAP:           0.9676
Avg query time: 1591 ms (slowed by rembg background removal)
Total queries:  29
```

Per-category P@5:
- Bananas / Grapes / Mangoes: **1.00** (perfect)
- Oranges: 0.95
- Apples: 0.90
- Strawberries: 0.80
- Peaches: 0.60
- Pomegranates: 0.47 (lowest — small dataset, similar color to Apples)

## Useful Commands

```bash
# Re-seed DB from scratch (clear + seed)
python app.py reset

# Just clear all data (no re-seed)
python app.py clear

# Run server without seeding
python app.py skip

# Regenerate ground truth
python infrastructure/AI_models/evaluation/build_ground_truth.py

# Run evaluation
python -m infrastructure.AI_models.evaluation.evaluate_fruit --mode api
python -m infrastructure.AI_models.evaluation.evaluate_fruit --weights 0.6,0.3,0.1
python -m infrastructure.AI_models.evaluation.evaluate_fruit --top-k 10

# Apply new migrations
export FLASK_APP=app.py
flask db migrate -m "your message"
flask db upgrade

# Check DB
docker compose exec db psql -U cbir_user -d fruit_cbir -c "SELECT COUNT(*) FROM features;"
```

## Team Status

### Member A — Data & Evaluation
- ✅ 7,147 images preprocessed (224×224, rembg)
- ✅ Ground truth: 29 queries
- ✅ Evaluation script (P@5, mAP)
- ⏳ Report data + evaluation sections

### Member B — Features & Search
- ✅ Color HSV + LBP texture + Hu Moments shape
- ✅ Weighted fusion + pgvector search
- ✅ Background removal pipeline
- ⏳ Report algorithm section

### Member C — Web & DB
- ✅ Flask Clean Architecture
- ✅ React frontend (drag-drop + weight tuning + charts)
- ✅ PostgreSQL + pgvector + Alembic migrations
- ⏳ Polish UI for demo
- ⏳ Report system section

## Known Issues / Notes
- **Python 3.11 required** (3.13 incompatible with llvmlite/numba pre-built wheels)
- **rembg** must be installed via `--no-deps` then add `pymatting` separately to avoid llvmlite source build
- Background removal adds ~1.5s per query — only needed for fresh user uploads, not for cached dataset features
- Pomegranates have lowest P@5 (47%) due to small dataset (310 images) and color similarity to red apples

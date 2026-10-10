# GeoMeasure Studio

**Geospatial File Measurement and Analysis Platform**

Upload KML or Shapefile ZIP archives and receive accurate, CRS-aware polygon area and line length measurements with an interactive map visualization.

---

## Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [API Documentation](#api-documentation)
- [CRS and Measurement Strategy](#crs-and-measurement-strategy)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Phase Roadmap](#phase-roadmap)

---

## Architecture

```
Browser (React + TypeScript + Vite)
    ↕  REST/JSON
FastAPI (Python 3.11)
  ├── File validation (extension, magic bytes, ZIP safety)
  ├── Geospatial processing (GeoPandas + Shapely + PyProj)
  ├── CRS-aware measurement (UTM auto-select / geodesic)
  └── Export (CSV, GeoJSON)
    ↕  asyncpg
PostgreSQL 16
```

**Key principle**: All measurements happen in Python. The frontend never calculates geometry — it displays results from the API.

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.11.x | `pyenv install 3.11.12` |
| Node.js | 20 LTS | https://nodejs.org |
| Docker Desktop | 4.x+ | https://www.docker.com/products/docker-desktop |
| Git | 2.x | pre-installed on macOS |

Verify all prerequisites:
```bash
python3 --version    # 3.11.x
node --version       # 20.x
docker --version     # 27.x
docker compose version  # v2.x
```

---

## Quick Start

```bash
# 1. Clone and enter the repo
git clone <repo-url> GeoMeasure-Studio
cd GeoMeasure-Studio

# 2. Start PostgreSQL
docker compose up -d db

# 3. Set up the backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# 4. Copy and review environment config
cp .env.example ../.env
# Edit ../.env if needed (defaults work for local development)

# 5. Run database migrations
alembic upgrade head

# 6. Start the API server
uvicorn app.main:app --reload --port 8000

# 7. Verify health
curl http://localhost:8000/health/
```

Expected health response when DB is running:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "db": "ok",
  "db_error": null,
  "environment": "development"
}
```

---

## Development Setup

### Backend (Python)

```bash
cd backend

# Create and activate virtualenv (Python 3.11 required)
python -m venv .venv
source .venv/bin/activate

# Install production + dev dependencies
pip install -r requirements-dev.txt

# Start development server with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Database

```bash
# Start PostgreSQL container
docker compose up -d db

# Check it's running
docker compose ps

# Run migrations (from backend/)
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "describe your change"
```

### Frontend (Phase 8+)

```bash
cd frontend
npm install
npm run dev
```

---

## Running Tests

```bash
cd backend
source .venv/bin/activate

# Run all tests
pytest

# Run only unit tests (no database required)
pytest tests/unit/ -m unit

# Run with coverage report
pytest --cov=app --cov-report=html

# Run a specific test file
pytest tests/integration/test_health.py -v
```

### Test Database

Integration tests that touch the database use the same PostgreSQL instance as development but connect to a `geomeasure_test` database (configured in `conftest.py` — Phase 6).

Unit tests (`tests/unit/`) run without any external services.

---

## API Documentation

Once the server is running, visit http://localhost:8000/docs for interactive API documentation.

### Current Endpoints (Phase 2)

| Method | Path | Description |
|---|---|---|
| GET | `/health/` | Application and database health status |

### Planned Endpoints (Phase 3–7)

| Method | Path | Description |
|---|---|---|
| POST | `/api/files/` | Upload and process a KML or Shapefile ZIP |
| GET | `/api/files/` | List uploaded files with pagination |
| GET | `/api/files/{id}/` | File detail and processing status |
| GET | `/api/files/{id}/measurements/` | Feature measurements with pagination |
| GET | `/api/files/{id}/features/` | Feature attributes and geometry |
| GET | `/api/files/{id}/summary/` | Aggregated statistics and warnings |
| GET | `/api/files/{id}/export/` | Download CSV or GeoJSON |
| DELETE | `/api/files/{id}/` | Delete file and all related data |

---

## CRS and Measurement Strategy

Accurate geospatial measurement requires careful handling of coordinate reference systems.

### Policy

| Situation | Action |
|---|---|
| File has a projected (metric) CRS | Use it directly |
| File has EPSG:4326 (degrees lat/lon) | Auto-select UTM zone from dataset centroid + warn |
| Dataset spans > 500 km or multiple UTM zones | Use geodesic calculation via PyProj Geod + warn |
| File has no readable CRS | Attempt auto-UTM if coordinates look like degrees; surface clear warning |

### Measurement methods

- **Polygon area ≤ 500 km extent**: UTM planar projection (error < 0.01%)
- **Polygon area > 500 km or global**: `pyproj.Geod.geometry_area_perimeter()` (geodesic)
- **Line length**: Always geodesic via `pyproj.Geod.geometry_length()`

The `measurement_crs` field in every API response records exactly which method was used.

### Never
- Calculate area from raw EPSG:4326 degree coordinates
- Silently assume CRS when metadata is missing
- Mix measurement CRS with display CRS (map always shows EPSG:4326)

---

## Project Structure

```
GeoMeasure-Studio/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app factory
│   │   ├── api/routes/          # HTTP endpoints (thin layer)
│   │   ├── core/                # Config, logging, exceptions
│   │   ├── schemas/             # Pydantic I/O contracts
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── services/            # All domain logic
│   │   ├── repositories/        # All database queries
│   │   └── db/                  # Session factory + base
│   ├── migrations/              # Alembic migration files
│   ├── tests/                   # Pytest test suite
│   ├── uploads/                 # Runtime file storage (gitignored)
│   └── requirements.txt
├── frontend/                    # React + TypeScript (Phase 8+)
├── docker-compose.yml           # PostgreSQL for development
├── .env.example                 # Environment variable template
└── README.md
```

---

## Environment Variables

Copy `.env.example` to `.env` in the project root. All variables have safe development defaults.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | asyncpg://... | PostgreSQL async connection URL |
| `DATABASE_URL_SYNC` | psycopg2://... | PostgreSQL sync URL (Alembic only) |
| `FRONTEND_ORIGINS` | localhost:5173 | CORS allowed origins |
| `MAX_UPLOAD_SIZE_MB` | 50 | Maximum file upload size |
| `MAX_ZIP_UNCOMPRESSED_MB` | 200 | ZIP bomb protection limit |
| `MAX_ZIP_ENTRIES` | 1000 | ZIP entry count limit |
| `LOG_FORMAT` | console | `json` (production) or `console` (dev) |
| `LOG_LEVEL` | INFO | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `DEBUG` | false | Enable SQLAlchemy query logging |

---

## Phase Roadmap

| Phase | Status | Description |
|---|---|---|
| 1 | ✅ Complete | Architecture and implementation plan |
| 2 | ✅ Complete | Repository setup, FastAPI, PostgreSQL, health endpoint |
| 3 | Planned | Secure file upload, format validation, initial tests |
| 4 | Planned | Geospatial reader, feature extraction, CRS detection |
| 5 | Planned | Measurement engine with CRS transformation |
| 6 | Planned | PostgreSQL persistence, SQLAlchemy models, migrations |
| 7 | Planned | Full REST API (files, measurements, features, exports) |
| 8 | Planned | React frontend scaffold, design system, upload UI |
| 9 | Planned | Frontend connected to real API, interactive map |
| 10 | Planned | Reports, history, pagination, loading/error states |
| 11 | Planned | Integration tests, security tests, performance |
| 12 | Planned | Docker Compose, deployment docs, final README |

---

## Contributing

This project follows a phase-by-phase development approach. Before contributing:

1. Read the architecture document (`phase1_architecture.md`)
2. Ensure tests pass: `pytest`
3. Check linting: `ruff check app/ tests/`
4. Follow the established service/repository layer boundaries

---

## License

MIT

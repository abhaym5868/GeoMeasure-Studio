FROM python:3.11-slim

# ── System dependencies ───────────────────────────────────────────
# libgdal-dev: required by Fiona/GDAL for geospatial I/O
# libgeos-dev: required by Shapely for geometry operations
# libproj-dev: required by PyProj for CRS transformations
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────
# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir -r requirements.txt

# ── Application code ──────────────────────────────────────────────
COPY . .

# Create runtime directories
RUN mkdir -p uploads tmp

# ── Non-root user for security ────────────────────────────────────
RUN useradd -m -u 1001 geomeasure && \
    chown -R geomeasure:geomeasure /app
USER geomeasure

# ── Runtime ───────────────────────────────────────────────────────
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

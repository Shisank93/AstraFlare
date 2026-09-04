# AstraFlare System Setup & Deployment Guide

**Project:** AstraFlare  
**Document:** Installation, Configuration & Operational Checklist  

---

## 1. Setup Categorization

### 1.1 Automatically Handled by AstraFlare System
- Source code generation & directory structure.
- FastAPI backend router endpoints & Pydantic validation schemas.
- Machine learning feature engineering & GBDT inference engine.
- React + TypeScript frontend dashboard & MapLibre map component.
- PostGIS database DDL schema creation & SQL migration scripts.
- Unit and integration tests.
- Docker Compose configuration and default environment variables.

---

### 1.2 Manual Actions Required by User

#### Step 1: Environment File Configuration
Copy the example environment template:
```bash
cp .env.example .env
```

#### Step 2: Obtain NASA FIRMS MAP_KEY
1. Go to the official NASA FIRMS API key portal: `https://firms.modaps.eosdis.nasa.gov/api/map_key/`
2. Register your email address to receive your 32-character `MAP_KEY`.
3. Open `.env` and set:
   ```env
   NASA_FIRMS_MAP_KEY=your_actual_nasa_firms_key_here
   ```
4. **Security Warning:** Never commit `.env` or hardcode API keys into version control.

#### Step 3: Install Required Python Dependencies
```bash
python3 -m pip install -r backend/requirements.txt
```
*(Dependencies include `fastapi`, `uvicorn`, `geopandas`, `shapely`, `lightgbm`, `scikit-learn`, `psycopg2-binary`, `sqlalchemy`, `geoalchemy2`)*.

#### Step 4: Database Setup (Choose Option A or B)

**Option A: Using Local PostgreSQL + PostGIS Service (Recommended for Native macOS)**
1. Ensure PostgreSQL is installed and started:
   ```bash
   brew services start postgresql
   ```
2. Enable PostGIS:
   ```bash
   brew install postgis
   createdb astraflare
   psql -d astraflare -c "CREATE EXTENSION IF NOT EXISTS postgis;"
   ```

**Option B: Using Docker Compose**
```bash
docker-compose up -d database
```

#### Step 5: Start Backend API Server
```bash
cd backend
python3 -m uvicorn main:app --reload --port 8000
```
Verify at `http://localhost:8000/docs`.

#### Step 6: Start Frontend React Application
```bash
cd frontend
npm install
npm run dev
```
Verify at `http://localhost:5173` or `http://localhost:3000`.

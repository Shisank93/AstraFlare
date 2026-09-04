# AstraFlare — AI-Powered Geospatial Thermal Intelligence Platform

> **Smart India Hackathon 2026 — Problem Statement SIH26162**

AstraFlare is an **AI-powered geospatial intelligence platform** that enriches satellite-detected thermal anomalies (NASA FIRMS) with industrial infrastructure, land-cover, historical recurrence, and environmental context to:
1. **Classify** the likely cause of an anomaly (Likely Industrial Incident, Persistent Industrial Heat, Natural/Wildland Fire, or Human Review Required),
2. **Estimate** its operational risk score (0.0 to 1.0),
3. **Explain** the reasoning and evidence behind each classification using TreeSHAP and GIS rules, and
4. **Prioritize** high-risk events requiring human analyst investigation.

---

## 🎯 Core Problem & Value Proposition

NASA FIRMS answers:
> *"Where is a thermal anomaly?"*

AstraFlare answers:
> *"What is this anomaly likely to represent, how unusual or risky is it, why does the system believe that, and should an analyst investigate it immediately?"*

---

## 🏗️ Architecture Overview

```text
NASA FIRMS Satellite Observation
               ↓
    PostGIS Database Storage
               ↓
    GIS Contextual Enrichment
 (OSM Infrastructure + WorldCover)
               ↓
 Feature Engineering & Ratio Calculation
               ↓
   LightGBM / CatBoost ML Model
               ↓
 Confidence Evaluation & Abstention Gate
 (Prob < 0.65 ──> Human Review Required)
               ↓
 Evidence Generation & Risk Engine
               ↓
  FastAPI REST / GeoJSON Endpoints
               ↓
 React + MapLibre Analyst Operations Dashboard
```

---

## 📂 Repository Structure

```text
AstraFlame/
├── backend/            # FastAPI REST API & Async Endpoints
├── frontend/           # React + TypeScript Analyst Operations Dashboard
├── ml/                 # Feature Engineering, LightGBM Training & SHAP Engine
├── data_pipeline/      # NASA FIRMS, OSM Overpass & ESA WorldCover Ingestion
├── database/           # PostGIS SQL Schemas & Migrations
├── scripts/            # Environment Setup & Data Preprocessing Helpers
├── tests/              # Backend, ML & Integration Test Suite
├── docs/               # System Specifications & Architecture Documentation
│   ├── requirements/   # Product Requirements Document (PRD)
│   ├── architecture/   # System, Database & Frontend Architecture + ADRs
│   ├── data/           # Data Architecture & Ingestion Specs
│   ├── gis/            # GIS Reference Systems & Spatial Query Specs
│   ├── ai/             # ML Model, Features & Weak Supervision Specs
│   ├── api/            # REST API Contracts & GeoJSON Specs
│   ├── demo/           # SIH Demonstration Scenarios
│   └── SETUP.md        # Installation & Manual Setup Guide
├── .env.example        # Environment Configuration Template
├── .gitignore          # Git Exclusion Rules
├── docker-compose.yml  # Containerized Service Definition
└── README.md           # Project Documentation Overview
```

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- PostgreSQL 14+ with PostGIS extension (or Docker)

### 1. Environment Setup
```bash
cp .env.example .env
```
*(Obtain your free NASA FIRMS key from `https://firms.modaps.eosdis.nasa.gov/api/map_key/` and paste into `.env`)*.

### 2. Full System Documentation
Detailed setup and architectural decisions can be found in `docs/`:
- [Environment Assessment](file:///Users/shisank_/Desktop/AstraFlame/docs/architecture/00_environment_assessment.md)
- [System Architecture](file:///Users/shisank_/Desktop/AstraFlame/docs/architecture/01_system_architecture.md)
- [Database Architecture](file:///Users/shisank_/Desktop/AstraFlame/docs/architecture/02_database_architecture.md)
- [Frontend Architecture](file:///Users/shisank_/Desktop/AstraFlame/docs/architecture/03_frontend_architecture.md)
- [Product Requirements](file:///Users/shisank_/Desktop/AstraFlame/docs/requirements/00_product_requirements.md)
- [Manual Setup Guide](file:///Users/shisank_/Desktop/AstraFlame/docs/SETUP.md)
- [Demonstration Scenarios](file:///Users/shisank_/Desktop/AstraFlame/docs/demo/00_demo_scenarios.md)

"""
Common Pydantic Schemas for AstraFlare API.
"""
from typing import Generic, TypeVar, List, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar("T")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall health status: 'healthy' or 'degraded'")
    mode: str = Field(default="REAL", description="AstraFlare operational mode")
    database: str = Field(..., description="Database connection status: 'connected' or 'disconnected'")
    postgis: str = Field(..., description="PostGIS extension status: 'available' or 'unavailable'")
    ml_model: str = Field(..., description="ML artifact status: 'available' or 'missing'")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Current deployment environment")

class ReadyResponse(BaseModel):
    status: str = Field(..., description="System readiness status: 'ready' or 'not_ready'")
    mode: str = Field(..., description="AstraFlare operational mode: 'REAL' or 'DEMO'")
    database: str = Field(..., description="Database engine: 'postgresql_postgis' or 'sqlite_fallback'")
    risk_engine: str = Field(..., description="Deterministic Risk Engine status")
    ml_status: str = Field(..., description="ML Model Baseline status")

class PaginationMeta(BaseModel):
    total: int = Field(..., description="Total matching record count")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total pages available")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T] = Field(..., description="List of dataset items")
    meta: PaginationMeta = Field(..., description="Pagination metadata")

class ErrorDetail(BaseModel):
    detail: str = Field(..., description="Error message description")
